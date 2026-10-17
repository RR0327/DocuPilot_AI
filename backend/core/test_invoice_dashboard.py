import csv
from datetime import timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import Document, ExtractedRecord


class InvoiceDashboardTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.alice = User.objects.create_user(username="billing_alice", password="test-password-123")
        self.bob = User.objects.create_user(username="billing_bob", password="test-password-123")
        self.client = APIClient()
        self.doc = Document.objects.create(owner=self.alice, title="Invoice α", file_type="txt")
        self.other_doc = Document.objects.create(owner=self.bob, title="Other", file_type="txt")
        self.today = timezone.localdate()

    def make_invoice(self, doc=None, due=None, total="120.00", currency="BDT", supplier="Supplier"):
        return ExtractedRecord.objects.create(
            document=doc or self.doc, record_type="invoice",
            extracted_data={"fields": {"invoice_number": "INV-1", "supplier": supplier,
                "due_date": due, "total": total, "currency": currency}},
            validation_status="unreviewed",
        )

    def set_status(self, record, status):
        response = self.client.patch(f"/api/invoices/{record.id}/payment-status/", {"payment_status": status}, format="json")
        self.assertEqual(response.status_code, 200, response.content)

    def test_explicit_payment_status_and_overdue_reporting(self):
        self.client.force_authenticate(self.alice)
        record = self.make_invoice(due=(self.today-timedelta(days=1)).isoformat())
        initial = self.client.get("/api/invoices/dashboard/").json()
        self.assertEqual(initial["payment_status_counts"]["unknown"], 1)
        self.assertEqual(initial["overdue_pending_count"], 0)
        self.assertEqual(initial["past_due_unconfirmed_count"], 1)
        self.set_status(record, "pending")
        data = self.client.get("/api/invoices/dashboard/").json()
        self.assertEqual(data["overdue_pending_count"], 1)
        self.assertEqual(data["pending_totals_by_currency"], {"BDT": "120.00"})
        self.assertEqual(self.client.get("/api/invoices/report/?due=overdue").json()["count"], 1)
        self.set_status(record, "paid")
        self.assertEqual(self.client.get("/api/invoices/dashboard/").json()["overdue_pending_count"], 0)

    def test_mixed_currencies_and_missing_amount_excluded(self):
        self.client.force_authenticate(self.alice)
        a = self.make_invoice(total="10.50", currency="USD")
        b = self.make_invoice(total="13.25", currency="BDT")
        c = self.make_invoice(total=None, currency="BDT")
        for r in (a,b,c): self.set_status(r, "pending")
        data = self.client.get("/api/invoices/dashboard/").json()
        self.assertEqual(data["pending_totals_by_currency"], {"BDT": "13.25", "USD": "10.50"})
        self.assertEqual(data["pending_without_usable_total_count"], 1)

    def test_filter_validation_and_due_dates(self):
        self.client.force_authenticate(self.alice)
        self.make_invoice(due=(self.today+timedelta(days=5)).isoformat())
        self.make_invoice(due=None)
        self.assertEqual(self.client.get("/api/invoices/report/?due=upcoming").json()["count"], 1)
        self.assertEqual(self.client.get("/api/invoices/report/?due=undated").json()["count"], 1)
        for q in ("?due=banana", "?due_from=2026-13-99", "?due_from=2026-10-20&due_to=2026-10-19", "?document_id=-1"):
            self.assertEqual(self.client.get("/api/invoices/report/"+q).status_code, 400)

    def test_csv_export_matches_filters_and_escapes_formulae(self):
        self.client.force_authenticate(self.alice)
        r = self.make_invoice(supplier="=HYPERLINK(123)")
        self.set_status(r, "pending")
        self.make_invoice(supplier="normal")
        resp = self.client.get("/api/invoices/export/?payment_status=pending")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("attachment", resp["Content-Disposition"])
        rows = list(csv.DictReader(StringIO(resp.content.decode("utf-8-sig"))))
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["supplier"].startswith("'="))
        self.assertEqual(rows[0]["payment_status"], "pending")

    def test_owner_isolation_across_all_endpoints(self):
        other = self.make_invoice(self.other_doc)
        mine = self.make_invoice()
        self.client.force_authenticate(self.alice)
        self.assertEqual(self.client.patch(f"/api/invoices/{other.pk}/payment-status/", {"payment_status": "paid"}, format="json").status_code, 404)
        self.assertEqual(self.client.get("/api/invoices/report/").json()["count"], 1)
        self.assertEqual(len(list(csv.DictReader(StringIO(self.client.get("/api/invoices/export/").content.decode("utf-8-sig"))))), 1)
        self.assertEqual(self.client.get("/api/invoices/dashboard/").json()["invoice_count"], 1)
        self.client.force_authenticate(user=None)
        for url in ("/api/invoices/report/", "/api/invoices/export/", "/api/invoices/dashboard/"):
            self.assertIn(self.client.get(url).status_code, (401,403))
        self.assertIn(self.client.patch(f"/api/invoices/{mine.pk}/payment-status/", {"payment_status": "paid"}, format="json").status_code, (401,403))

    def test_invalid_payment_state_and_old_invoice_api(self):
        self.client.force_authenticate(self.alice)
        record = self.make_invoice()
        self.assertEqual(self.client.patch(f"/api/invoices/{record.pk}/payment-status/", {"payment_status": "overdue"}, format="json").status_code, 400)
        self.assertEqual(self.client.get("/api/invoices/").status_code, 200)
        self.assertEqual(self.client.get("/api/health/").json()["status"], "ok")
