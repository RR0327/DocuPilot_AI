"""Owner-scoped invoice value analytics, not cash expenditure accounting.

Uses reviewed corrections only when approved. Never converts or mixes currencies.
"""
from collections import defaultdict
from datetime import date
from decimal import Decimal

from .invoice_dashboard import _amount, _iso_date, invoices_for_user, payment_status
from .review import current_fields

CURRENCIES = frozenset(("BDT", "USD", "EUR", "GBP"))


def analytics_for_user(user, *, currency=None, year=None, limit=10):
    if currency is not None and currency not in CURRENCIES:
        raise ValueError("currency must be BDT, USD, EUR or GBP")
    if year is not None and (type(year) is not int or year < 2000 or year > 2100):
        raise ValueError("year must be between 2000 and 2100")
    if type(limit) is not int or limit < 1 or limit > 50:
        raise ValueError("limit must be between 1 and 50")
    supplier_totals = defaultdict(lambda: Decimal("0"))
    monthly_totals = defaultdict(lambda: Decimal("0"))
    currency_totals = defaultdict(lambda: Decimal("0"))
    status_counts = defaultdict(int)
    included = 0
    excluded = defaultdict(int)
    for record in invoices_for_user(user):
        if record.validation_status == "invalid":
            excluded["rejected"] += 1
            continue
        fields = current_fields(record)
        invoice_currency = fields.get("currency")
        if currency and invoice_currency != currency:
            continue
        amount = _amount(fields.get("total"))
        if amount is None:
            excluded["invalid_or_missing_total"] += 1
            continue
        if invoice_currency not in CURRENCIES:
            excluded["invalid_or_missing_currency"] += 1
            continue
        invoice_date = _iso_date(fields.get("invoice_date"))
        if invoice_date is None:
            excluded["invalid_or_missing_invoice_date"] += 1
            continue
        if year is not None and invoice_date.year != year:
            continue
        supplier = fields.get("supplier")
        supplier = supplier.strip() if isinstance(supplier, str) else ""
        if not supplier:
            excluded["missing_supplier"] += 1
            continue
        if len(supplier) > 255:
            excluded["invalid_supplier"] += 1
            continue
        included += 1
        currency_totals[invoice_currency] += amount
        supplier_totals[(invoice_currency, supplier)] += amount
        monthly_totals[(invoice_currency, invoice_date.strftime("%Y-%m"))] += amount
        status_counts[payment_status(record)] += 1

    def money(value):
        return str(value.quantize(Decimal("0.01")))

    suppliers = [{"currency": code, "supplier": name, "invoice_total": money(amount)}
                 for (code, name), amount in supplier_totals.items()]
    suppliers.sort(key=lambda row: (row["currency"], -Decimal(row["invoice_total"]), row["supplier"].casefold()))
    months = [{"currency": code, "month": month, "invoice_total": money(amount)}
              for (code, month), amount in sorted(monthly_totals.items(), key=lambda x: (x[0][0], x[0][1]))]
    return {
        "basis": "invoice_value_not_cash_spend",
        "date_basis": "invoice_date",
        "currency_filter": currency,
        "year_filter": year,
        "included_invoice_count": included,
        "excluded_invoice_counts": dict(sorted(excluded.items())),
        "included_payment_status_counts": dict(sorted(status_counts.items())),
        "totals_by_currency": {code: money(value) for code, value in sorted(currency_totals.items())},
        "monthly_trends": months,
        "top_suppliers": suppliers[:limit],
        "supplier_count": len(supplier_totals),
        "supplier_limit": limit,
    }
