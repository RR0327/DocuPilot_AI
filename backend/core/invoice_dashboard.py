"""Owner-scoped invoice reports; no inferred payment confirmations or cross-currency summing."""
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from io import StringIO

from django.db.models import Prefetch
from django.utils import timezone

from .models import ExtractedRecord, InvoicePaymentState

VALID_STATUSES = set(InvoicePaymentState.State.values)
COLUMNS = ("record_id", "document_id", "document_title", "invoice_number", "supplier", "invoice_date", "due_date", "subtotal", "tax", "total", "currency", "payment_status", "due_category", "validation_status")


def _iso_date(raw):
    if not isinstance(raw, str):
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def _amount(raw):
    if not isinstance(raw, (int, str)) or isinstance(raw, bool):
        return None
    try:
        value = Decimal(str(raw))
        if not value.is_finite() or value < 0:
            return None
        return value
    except (InvalidOperation, ValueError):
        return None


def payment_status(record):
    try:
        return record.payment_state.status
    except InvoicePaymentState.DoesNotExist:
        return InvoicePaymentState.State.UNKNOWN


def serialize_invoice(record, today=None):
    today = today or timezone.localdate()
    data = record.extracted_data if isinstance(record.extracted_data, dict) else {}
    fields = data.get("fields") if isinstance(data.get("fields"), dict) else {}
    due = _iso_date(fields.get("due_date"))
    status = payment_status(record)
    due_category = "undated"
    if due:
        due_category = "overdue" if due < today else "due_today" if due == today else "upcoming"
    # "overdue" is a payment claim and requires an explicitly pending state.
    if status != "pending" and due_category == "overdue":
        due_category = "past_due_unconfirmed"
    return {
        "record_id": record.pk, "document_id": record.document_id,
        "document_title": record.document.title,
        "invoice_number": fields.get("invoice_number"), "supplier": fields.get("supplier"),
        "invoice_date": fields.get("invoice_date"), "due_date": fields.get("due_date"),
        "subtotal": fields.get("subtotal"), "tax": fields.get("tax"),
        "total": fields.get("total"), "currency": fields.get("currency"),
        "payment_status": status, "due_category": due_category,
        "validation_status": record.validation_status,
    }


def invoices_for_user(user):
    return ExtractedRecord.objects.filter(document__owner=user, record_type="invoice").select_related("document", "payment_state").order_by("-created_at", "-pk")


def filtered_invoices(user, params, today=None):
    today = today or timezone.localdate()
    allowed = {"payment_status", "due", "due_from", "due_to", "document_id"}
    if any(key not in allowed for key in params):
        raise ValueError("Unsupported filter parameter")
    status = params.get("payment_status")
    if status and status not in VALID_STATUSES:
        raise ValueError("Invalid payment_status")
    due_filter = params.get("due")
    if due_filter and due_filter not in {"overdue", "due_today", "upcoming", "undated", "past_due_unconfirmed"}:
        raise ValueError("Invalid due filter")
    start = params.get("due_from")
    end = params.get("due_to")
    if start and not _iso_date(start):
        raise ValueError("due_from must be YYYY-MM-DD")
    if end and not _iso_date(end):
        raise ValueError("due_to must be YYYY-MM-DD")
    if start and end and start > end:
        raise ValueError("due_from cannot exceed due_to")
    document_id = params.get("document_id")
    if document_id is not None and (not document_id.isdecimal() or int(document_id) <= 0):
        raise ValueError("document_id must be a positive integer")
    records = invoices_for_user(user)
    if document_id:
        records = records.filter(document_id=int(document_id))
    result = []
    for record in records:
        item = serialize_invoice(record, today)
        if status and item["payment_status"] != status: continue
        if due_filter and item["due_category"] != due_filter: continue
        due = _iso_date(item["due_date"])
        if start and (due is None or due < _iso_date(start)): continue
        if end and (due is None or due > _iso_date(end)): continue
        result.append(item)
    return result


def dashboard(user, today=None):
    today = today or timezone.localdate()
    rows = [serialize_invoice(record, today) for record in invoices_for_user(user)]
    counts = {key: sum(x["payment_status"] == key for x in rows) for key in VALID_STATUSES}
    overdue = [x for x in rows if x["due_category"] == "overdue"]
    totals = {}
    excluded = 0
    for row in rows:
        if row["payment_status"] != "pending":
            continue
        amt = _amount(row["total"])
        currency = row["currency"]
        if amt is None or currency not in {"BDT", "USD", "EUR", "GBP"}:
            excluded += 1
            continue
        totals[currency] = totals.get(currency, Decimal("0")) + amt
    return {
        "as_of_date": today.isoformat(), "invoice_count": len(rows),
        "payment_status_counts": counts, "overdue_pending_count": len(overdue),
        "due_today_pending_count": sum(x["due_category"] == "due_today" and x["payment_status"] == "pending" for x in rows),
        "pending_totals_by_currency": {k: str(v.quantize(Decimal("0.01"))) for k, v in sorted(totals.items())},
        "pending_without_usable_total_count": excluded,
        "past_due_unconfirmed_count": sum(x["due_category"] == "past_due_unconfirmed" for x in rows),
    }


def export_csv(rows):
    stream = StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        # Stop spreadsheet applications from interpreting untrusted strings as formulas.
        cleaned = {}
        for key in COLUMNS:
            value = row.get(key)
            value = "" if value is None else str(value)
            if value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r", "\n")):
                value = "'" + value
            cleaned[key] = value
        writer.writerow(cleaned)
    return "\ufeff" + stream.getvalue()
