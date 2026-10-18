"""Step 4 line-item extraction, arithmetic, persistence, and owner isolation."""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from .line_items import parse_line_items
from .models import Document, DocumentPage, InvoiceLineItem, ExtractedRecord


class LineItemTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.owner = User.objects.create_user(username="line_owner", password="secure-password-123")
        cls.other = User.objects.create_user(username="line_other", password="secure-password-123")

    def setUp(self):
        self.document = Document.objects.create(owner=self.owner, title="Item Invoice", file_type="txt", processing_status="completed")
        self.page = DocumentPage.objects.create(document=self.document, page_number=2, extracted_text=(
            "Invoice No: ITEM-44\nSupplier: Example Ltd\nDescription | Qty | Unit Price | Amount\n"
            "Ceramic Tile | 2 | 125.50 | 251.00\nTransport Fee | 1 | 20.00 | 21.00\n"
            "Subtotal: BDT 272.00\nTotal Amount: BDT 272.00"
        ))
        self.client = APIClient()
        self.client.force_authenticate(self.owner)

    def test_line_parser_page_and_validation(self):
        items, warnings = parse_line_items([self.page])
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["description"], "Ceramic Tile")
        self.assertEqual(items[0]["page_number"], 2)
        self.assertEqual(items[0]["calculated_total"], "251.00")
        self.assertEqual(items[0]["validation_status"], "matched")
        self.assertEqual(items[1]["validation_status"], "mismatch")
        self.assertIn("Transport Fee", items[1]["source_excerpt"])
        self.assertEqual(len(warnings), 1)

    def test_requires_explicit_table_heading(self):
        self.page.extracted_text = "Invoice No: A1\nCeramic Tile | 2 | 125.50 | 251.00"
        items, warnings = parse_line_items([self.page])
        self.assertEqual((items, warnings), ([], []))

    def test_no_inference_for_missing_columns(self):
        self.page.extracted_text = "Invoice No: B2\nDescription Qty Unit Price Total\nTile 2 100\nTotal: 200"
        self.assertEqual(parse_line_items([self.page])[0], [])

    def test_end_to_end_persistence_and_owner_scope(self):
        url = f"/api/documents/{self.document.id}/invoice/extract/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, 201, response.content)
        record_id = response.json()["id"]
        self.assertEqual(InvoiceLineItem.objects.filter(record_id=record_id).count(), 2)
        self.assertEqual(response.json()["extracted_data"]["line_item_count"], 2)
        self.assertEqual(response.json()["validation_status"], "unreviewed")
        detail_url = f"/api/invoices/{record_id}/line-items/"
        detail = self.client.get(detail_url)
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["count"], 2)
        self.assertEqual(Decimal(detail.json()["results"][0]["quantity"]), Decimal("2"))
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(detail_url).status_code, 404)
        self.assertEqual(self.client.post(url).status_code, 404)
        self.client.force_authenticate(user=None)
        self.assertIn(self.client.get(detail_url).status_code, (401, 403))

    def test_reextraction_creates_new_record_without_mutating_old(self):
        url = f"/api/documents/{self.document.id}/invoice/extract/"
        first = self.client.post(url).json()["id"]
        self.page.extracted_text = "Invoice No: ITEM-45\nDescription Qty Unit Price Total\nNew Item 3 10.00 30.00"
        self.page.save()
        second = self.client.post(url).json()["id"]
        self.assertNotEqual(first, second)
        self.assertEqual(InvoiceLineItem.objects.filter(record_id=first).count(), 2)
        self.assertEqual(InvoiceLineItem.objects.filter(record_id=second).count(), 1)
        self.document.delete()
        self.assertFalse(ExtractedRecord.objects.filter(pk=first).exists())
        self.assertEqual(InvoiceLineItem.objects.count(), 0)
