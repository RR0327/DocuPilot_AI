"""Regression tests for owner-scoped, currency-safe analytics."""
from datetime import date
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from .models import Document, ExtractedRecord
from .supplier_analytics import analytics_for_user
from .review import apply_review


class SupplierAnalyticsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username="analytics_owner", password="test-password-123")
        self.other = User.objects.create_user(username="analytics_other", password="test-password-123")
        self.document = Document.objects.create(owner=self.owner, title="Bills", file_type="txt")
        self.other_document = Document.objects.create(owner=self.other, title="Private", file_type="txt")
        self.client = APIClient()
        self.client.force_authenticate(self.owner)

    def make_invoice(self, *, owner=False, supplier="Acme", total="100.00", currency="BDT", invoice_date="2026-08-12"):
        return ExtractedRecord.objects.create(
            document=self.other_document if owner else self.document,
            record_type="invoice", validation_status="unreviewed",
            extracted_data={"fields": {"supplier": supplier, "total": total,
                                        "currency": currency, "invoice_date": invoice_date}})

    def test_currency_isolation_months_suppliers_and_year(self):
        self.make_invoice()
        self.make_invoice(total="25.00", invoice_date="2026-09-01")
        self.make_invoice(supplier="Beta", currency="USD", total="7.50")
        self.make_invoice(owner=True, total="999999.00")
        data = self.client.get("/api/invoices/analytics/").json()
        self.assertEqual(data["included_invoice_count"], 3)
        self.assertEqual(data["totals_by_currency"], {"BDT": "125.00", "USD": "7.50"})
        self.assertEqual(len(data["monthly_trends"]), 3)
        self.assertEqual(len(data["top_suppliers"]), 2)
        usd = self.client.get("/api/invoices/analytics/?currency=USD&year=2026").json()
        self.assertEqual(usd["totals_by_currency"], {"USD": "7.50"})
        self.assertEqual(usd["included_invoice_count"], 1)

    def test_approved_review_applies_and_reopen_resets(self):
        record = self.make_invoice(total="100.00")
        apply_review(record.id, self.owner, {"action": "approve", "corrections": {"total": "250.00", "supplier": "Reviewed"}})
        data = self.client.get("/api/invoices/analytics/").json()
        self.assertEqual(data["totals_by_currency"], {"BDT": "250.00"})
        self.assertEqual(data["top_suppliers"][0]["supplier"], "Reviewed")
        apply_review(record.id, self.owner, {"action": "reopen"})
        data = self.client.get("/api/invoices/analytics/").json()
        self.assertEqual(data["totals_by_currency"], {"BDT": "100.00"})

    def test_invalid_and_missing_fields_are_excluded(self):
        invalid = self.make_invoice(total="500.00")
        apply_review(invalid.id, self.owner, {"action": "reject", "note": "Wrong invoice"})
        self.make_invoice(total="nan")
        self.make_invoice(currency="XYZ")
        self.make_invoice(invoice_date="bad-date")
        self.make_invoice(supplier="  ")
        data = analytics_for_user(self.owner)
        self.assertEqual(data["included_invoice_count"], 0)
        self.assertEqual(data["excluded_invoice_counts"], {
            "invalid_or_missing_currency": 1, "invalid_or_missing_invoice_date": 1,
            "invalid_or_missing_total": 1, "missing_supplier": 1, "rejected": 1})

    def test_filters_and_authentication(self):
        self.make_invoice()
        for query in ("?currency=GBPX", "?year=oops", "?year=1999", "?limit=0", "?limit=51", "?unused=1"):
            self.assertEqual(self.client.get("/api/invoices/analytics/" + query).status_code, 400)
        self.assertEqual(self.client.get("/api/invoices/analytics/?limit=1").status_code, 200)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get("/api/invoices/analytics/").json()["included_invoice_count"], 0)
        self.client.force_authenticate(user=None)
        self.assertIn(self.client.get("/api/invoices/analytics/").status_code, (401, 403))

    def test_year_and_date_validation(self):
        self.make_invoice(invoice_date="2025-12-01", total="15.00")
        self.make_invoice(invoice_date="2026-01-01", total="5.00")
        response = self.client.get("/api/invoices/analytics/?year=2026").json()
        self.assertEqual(response["totals_by_currency"], {"BDT": "5.00"})
        self.assertEqual(response["monthly_trends"][0]["month"], "2026-01")
