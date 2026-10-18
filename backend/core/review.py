"""Safe, owner-only invoice review without rewriting source extraction or evidence."""
from decimal import Decimal, InvalidOperation
from datetime import date
from django.db import transaction
from rest_framework.exceptions import ValidationError
from .models import ExtractedRecord, ExtractionReview

FIELDS = ("invoice_number", "supplier", "invoice_date", "due_date", "subtotal", "tax", "total", "currency")
MONEY = {"subtotal", "tax", "total"}


def clean_corrections(value):
    if not isinstance(value, dict) or not value or len(value) > len(FIELDS):
        raise ValidationError({"corrections": "Provide a nonempty object of recognized invoice fields."})
    result = {}
    for key, raw in value.items():
        if key not in FIELDS or (raw is not None and not isinstance(raw, str)):
            raise ValidationError({"corrections": f"Invalid field or value: {key}"})
        text = raw.strip() if isinstance(raw, str) else None
        if text is not None and (not text or len(text) > 255):
            raise ValidationError({"corrections": f"Invalid value for {key}"})
        if key in MONEY and text is not None:
            try:
                num = Decimal(text)
                if not num.is_finite() or num < 0 or num > Decimal("999999999999.99") or num.as_tuple().exponent < -2:
                    raise ValueError()
                text = f"{num:.2f}"
            except (InvalidOperation, ValueError):
                raise ValidationError({"corrections": f"{key} must be a valid nonnegative amount with up to 2 decimals"})
        if key in ("invoice_date", "due_date") and text is not None:
            try:
                if date.fromisoformat(text).isoformat() != text:
                    raise ValueError()
            except ValueError:
                raise ValidationError({"corrections": f"{key} must be YYYY-MM-DD"})
        if key == "currency" and text is not None:
            text = text.upper()
            if text not in ("BDT", "USD", "EUR", "GBP"):
                raise ValidationError({"corrections": "Unsupported currency"})
        result[key] = text
    return result


def quality_flags(record):
    data = record.extracted_data or {}
    flags = list(data.get("warnings") or []) + list(data.get("line_item_warnings") or [])
    if data.get("missing_fields"):
        flags.append("Missing extracted invoice fields")
    if record.line_items.filter(validation_status="mismatch").exists():
        flags.append("Line-item arithmetic mismatch")
    return list(dict.fromkeys(str(f) for f in flags))


def current_fields(record):
    fields = dict((record.extracted_data or {}).get("fields") or {})
    latest = record.reviews.first()
    # Only the latest approved review is authoritative; reopen/reject resets verification.
    if latest and latest.action == "approve" and latest.new_status == ExtractedRecord.ValidationStatus.VALID:
        fields.update(latest.corrections)
    return fields


def review_details(record):
    return {
        "record_id": record.pk, "document_id": record.document_id, "document_title": record.document.title,
        "validation_status": record.validation_status,
        "original_fields": (record.extracted_data or {}).get("fields", {}),
        "effective_fields": current_fields(record),
        "source_references": (record.extracted_data or {}).get("source_references", {}),
        "quality_flags": quality_flags(record),
        "history": [{"id": r.id, "action": r.action, "previous_status": r.previous_status,
                     "new_status": r.new_status, "corrections": r.corrections, "note": r.note,
                     "reviewed_at": r.reviewed_at.isoformat(), "reviewer_id": r.reviewer_id}
                    for r in record.reviews.all()],
    }


@transaction.atomic
def apply_review(record_id, owner, payload):
    record = ExtractedRecord.objects.select_for_update().select_related("document").get(
        pk=record_id, document__owner=owner, record_type="invoice"
    )
    if not isinstance(payload, dict) or set(payload) - {"action", "corrections", "note"}:
        raise ValidationError({"detail": "Only action, corrections and note are supported."})
    action = payload.get("action")
    if action not in ("approve", "reject", "reopen"):
        raise ValidationError({"action": "Choose approve, reject or reopen."})
    note = payload.get("note", "")
    if not isinstance(note, str) or len(note) > 2000:
        raise ValidationError({"note": "Note must be at most 2000 characters."})
    if action == "reopen":
        if record.validation_status == "unreviewed" or payload.get("corrections") is not None:
            raise ValidationError({"action": "Only reviewed invoices can be reopened; no corrections allowed."})
        corrections = {}
        new_status = "unreviewed"
    else:
        if record.validation_status != "unreviewed":
            raise ValidationError({"action": "Reopen an existing decision before reviewing again."})
        if action == "reject" and not note.strip():
            raise ValidationError({"note": "A rejection reason is required."})
        corrections = clean_corrections(payload["corrections"]) if "corrections" in payload else {}
        if action == "reject" and corrections:
            raise ValidationError({"corrections": "Corrections are only accepted with approval."})
        new_status = "valid" if action == "approve" else "invalid"
    previous = record.validation_status
    ExtractionReview.objects.create(record=record, reviewer=owner, action=action,
        previous_status=previous, new_status=new_status, corrections=corrections, note=note.strip())
    record.validation_status = new_status
    record.save(update_fields=["validation_status"])
    return record
