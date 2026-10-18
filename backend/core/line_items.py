"""Conservative invoice table-row extraction. Never infer missing financial columns."""
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

# Recognize explicit columns, not arbitrary numerical text in business documents.
HEADER = re.compile(r"(?i)\b(?:item|description|product|service)\b.*\b(?:qty|quantity)\b.*\b(?:unit\s*price|rate|price)\b.*\b(?:amount|total)\b")
MONEY = r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{1,2})?"
QTY = r"\d+(?:\.\d{1,3})?"
ROW = re.compile(rf"^(.{{2,255}}?)\s+(?P<qty>{QTY})\s+(?P<price>{MONEY})\s+(?P<total>{MONEY})$")
SKIP = re.compile(r"(?i)^\s*(?:subtotal|sub-total|tax|vat|grand total|total|discount|shipping|invoice|balance|due|page)\b")
CENT = Decimal("0.01")


def parse_line_items(pages):
    """Find rows only after a recognizable header on the same page.

    Supports pipe-separated or aligned text rows. No arithmetic guessing, and
    malformed or ambiguous rows are ignored. Returns (items, warnings).
    """
    result, warnings = [], []
    for page in pages:
        active = False
        for raw in page.extracted_text.splitlines():
            line = " ".join(raw.strip().split())
            if HEADER.search(line):
                active = True
                continue
            if not active or not line:
                continue
            if SKIP.match(line):
                active = False
                continue
            normalized = " ".join(part.strip() for part in line.split("|") if part.strip())
            match = ROW.fullmatch(normalized)
            if not match:
                continue
            desc = match.group(1).strip()
            if SKIP.match(desc) or len(desc) > 255:
                continue
            try:
                qty = Decimal(match.group("qty"))
                price = Decimal(match.group("price").replace(",", ""))
                total = Decimal(match.group("total").replace(",", ""))
                computed = (qty * price).quantize(CENT, rounding=ROUND_HALF_UP)
            except (InvalidOperation, ValueError):
                continue
            if not (Decimal("0") < qty <= Decimal("99999999999.999")) or price < 0 or total < 0 or price > Decimal("99999999999999.99") or total > Decimal("99999999999999.99") or computed > Decimal("99999999999999.99"):
                continue
            status = "matched" if abs(computed - total) <= CENT else "mismatch"
            item = {
                "line_number": len(result) + 1,
                "description": desc,
                "quantity": str(qty),
                "unit_price": f"{price:.2f}",
                "line_total": f"{total:.2f}",
                "calculated_total": f"{computed:.2f}",
                "validation_status": status,
                "page_number": page.page_number,
                "source_excerpt": line[:500],
            }
            result.append(item)
            if status == "mismatch":
                warnings.append(f"Line item {item['line_number']}: quantity × unit price differs from line total; review required")
            if len(result) >= 500:
                warnings.append("Line item limit reached (500); review document manually")
                return result, warnings
    return result, warnings
