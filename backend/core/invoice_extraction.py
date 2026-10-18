"""Conservative, explainable rule-based invoice parsing from saved DocumentPage text.

Unknown fields remain null. Evidence includes the exact page number and matching line.
No LLM, guessing, or payment status inference is performed.
"""
import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from django.db import transaction
from .models import Document, ExtractedRecord


class InvoiceError(Exception):
    pass


LABELS = {
    "invoice_number": r"(?:invoice\s*(?:number|no\.?|#)|inv\s*(?:no\.?|#))",
    "invoice_date": r"(?:invoice\s*date|date\s*of\s*invoice|issued?\s*(?:on|date))",
    "due_date": r"(?:payment\s*due(?:\s*date)?|due\s*date|pay\s*by)",
    "subtotal": r"(?:sub[ -]?total|net\s*amount)",
    "tax": r"(?:total\s*(?:vat|tax)|vat(?:\s*amount)?|tax(?:\s*amount)?)",
    "total": r"(?:(?:grand|invoice|amount)\s*total|total\s*(?:amount|due|payable)?|balance\s*due)",
    "supplier": r"(?:supplier|vendor|seller|bill\s*from|issued\s*by)",
}
AMOUNT = re.compile(r"(?:(?P<before>BDT|USD|EUR|GBP|Tk\.?|৳|\$|€|£)\s*)?(?P<amount>-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{1,2})?)(?:\s*(?P<after>BDT|USD|EUR|GBP|Tk\.?|৳|\$|€|£))?", re.I)
CURRENCY = {"BDT":"BDT","TK":"BDT","৳":"BDT","USD":"USD","$":"USD","EUR":"EUR","€":"EUR","GBP":"GBP","£":"GBP"}
DATE_PATTERN = re.compile(r"\b(?:\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})\b")
FIELDS = ("invoice_number", "supplier", "invoice_date", "subtotal", "tax", "total", "due_date", "currency")


def _date(value):
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    # Numeric ambiguous US-format dates are intentionally not inferred.
    return None


def _money(value):
    matches = list(AMOUNT.finditer(value))
    # A labeled line's last number is usually the amount; do not parse a percentage as money.
    for match in reversed(matches):
        if match.end() < len(value) and value[match.end():].lstrip().startswith('%'):
            continue
        try:
            amount = Decimal(match.group('amount').replace(',', ''))
        except InvalidOperation:
            continue
        if amount < 0 or amount > Decimal('999999999999.99'):
            continue
        token = (match.group('before') or match.group('after') or '').upper().rstrip('.')
        return format(amount, '.2f'), CURRENCY.get(token)
    return None, None


def _evidence(page_number, line):
    return {"page_number": page_number, "excerpt": line[:500]}


def parse_invoice_pages(pages):
    """Return structured extracted_data with null unknowns and page-level evidence."""
    values = {field: None for field in FIELDS}
    evidence = {}
    currencies = set()
    for page in pages:
        for raw in page.extracted_text.splitlines():
            line = ' '.join(raw.split())
            if not line:
                continue
            for field, expression in LABELS.items():
                if values[field] is not None:
                    continue
                match = re.search(r"^\s*" + expression + r"\s*[:#–-]?\s*", line, re.I)
                if not match:
                    continue
                remainder = line[match.end():].strip()
                result = None
                currency = None
                if field in ('subtotal', 'tax', 'total'):
                    # Don't treat a bare tax rate (e.g., VAT 15%) as an amount.
                    result, currency = _money(remainder)
                elif field in ('invoice_date', 'due_date'):
                    found = DATE_PATTERN.search(remainder)
                    result = _date(found.group(0)) if found else None
                elif field == 'invoice_number':
                    found = re.match(r"[A-Za-z0-9][A-Za-z0-9./_-]{0,79}", remainder)
                    result = found.group(0) if found else None
                else:
                    result = remainder[:255] if remainder and len(remainder) <= 255 else None
                if result is not None:
                    values[field] = result
                    evidence[field] = _evidence(page.page_number, line)
                    if currency:
                        currencies.add(currency)
    if len(currencies) == 1:
        values['currency'] = next(iter(currencies))
        for key in ('total', 'subtotal', 'tax'):
            if key in evidence:
                evidence['currency'] = evidence[key]
                break
    warnings = []
    if len(currencies) > 1:
        warnings.append('Conflicting currencies; manual verification required')
    if values['subtotal'] and values['tax'] and values['total']:
        if Decimal(values['subtotal']) + Decimal(values['tax']) != Decimal(values['total']):
            warnings.append('Subtotal plus tax differs from total; manual review required')
    missing = [field for field in FIELDS if values[field] is None]
    return {'fields': values, 'source_references': evidence, 'missing_fields': missing, 'warnings': warnings, 'extraction_method': 'rule_based_v1'}


def extract_invoice(document):
    if document.processing_status != Document.Status.COMPLETED:
        raise InvoiceError('Extract document text successfully before invoice extraction')
    pages = list(document.pages.order_by('page_number'))
    if not pages or not any(page.extracted_text.strip() for page in pages):
        raise InvoiceError('No extracted text is available')
    data = parse_invoice_pages(pages)
    if not any(data['fields'][key] for key in ('invoice_number', 'supplier', 'total', 'invoice_date')):
        raise InvoiceError('No recognizable invoice fields found; record not saved')
    # Always unreviewed: syntactically valid extracted values are not independently verified.
    with transaction.atomic():
        record = ExtractedRecord.objects.create(
            document=document, record_type='invoice', extracted_data=data,
            validation_status=ExtractedRecord.ValidationStatus.UNREVIEWED,
        )
    return record
