import tempfile
from pathlib import Path
from unittest.mock import patch

import fitz
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .extraction import ExtractionError, extract_document
from .models import Document, DocumentPage


class DocumentExtractionTests(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        override = override_settings(MEDIA_ROOT=self.temp_dir.name)
        override.enable()
        self.addCleanup(override.disable)
        user = get_user_model()
        self.alice = user.objects.create_user(username="alice_extract", password="demo-password-123")
        self.bob = user.objects.create_user(username="bob_extract", password="demo-password-123")
        self.client = APIClient()
        self.client.force_authenticate(self.alice)

    def upload(self, name, content):
        response = self.client.post("/api/documents/upload/", {
            "file": SimpleUploadedFile(name, content), "title": "Evidence sample"
        }, format="multipart")
        self.assertEqual(response.status_code, 201, response.content)
        return Document.objects.get(id=response.json()["id"])

    @staticmethod
    def make_pdf():
        with fitz.open() as pdf:
            for text in ["First page: invoice 42", "Second page: total BDT 500"]:
                page = pdf.new_page()
                page.insert_text((72, 72), text)
            return pdf.tobytes()

    def test_pdf_two_pages_and_retry_idempotent(self):
        doc = self.upload("invoice.pdf", self.make_pdf())
        url = f"/api/documents/{doc.pk}/extract/"
        for _ in range(2):
            response = self.client.post(url)
            self.assertEqual(response.status_code, 200, response.content)
            self.assertEqual(response.json()["processing_status"], "completed")
            self.assertEqual(response.json()["page_count"], 2)
            doc.refresh_from_db()
            self.assertEqual(doc.processing_status, Document.Status.COMPLETED)
            pages = self.client.get(f"/api/documents/{doc.pk}/pages/").json()
            self.assertEqual([p["page_number"] for p in pages], [1, 2])
            self.assertIn("invoice 42", pages[0]["extracted_text"])
            self.assertIn("BDT 500", pages[1]["extracted_text"])
            self.assertEqual(DocumentPage.objects.filter(document=doc).count(), 2)

    def test_txt_utf8_bangla_is_single_logical_page(self):
        doc = self.upload("notes.txt", "Hello বাংলা document".encode("utf-8"))
        response = self.client.post(f"/api/documents/{doc.pk}/extract/")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["page_count"], 1)
        self.assertEqual(doc.pages.first().extracted_text, "Hello বাংলা document")

    def test_fake_header_only_pdf_is_rejected_without_pages(self):
        doc = self.upload("fake.pdf", b"%PDF-not-real")
        response = self.client.post(f"/api/documents/{doc.pk}/extract/")
        self.assertEqual(response.status_code, 422)
        doc.refresh_from_db()
        self.assertEqual(doc.processing_status, Document.Status.FAILED)
        self.assertFalse(doc.pages.exists())

    def test_scanned_pdf_without_text_requires_ocr(self):
        with fitz.open() as pdf:
            pdf.new_page()
            raw = pdf.tobytes()
        doc = self.upload("scanned.pdf", raw)
        response = self.client.post(f"/api/documents/{doc.pk}/extract/")
        self.assertEqual(response.status_code, 422)
        self.assertIn("OCR", response.json()["detail"])
        self.assertEqual(self.client.get(f"/api/documents/{doc.pk}/pages/").json(), [])

    def test_missing_file_metadata_record_fails(self):
        doc = Document.objects.create(owner=self.alice, title="Legacy metadata")
        response = self.client.post(f"/api/documents/{doc.pk}/extract/")
        self.assertEqual(response.status_code, 422)
        doc.refresh_from_db()
        self.assertEqual(doc.processing_status, Document.Status.FAILED)

    def test_other_user_cannot_extract_or_read_pages(self):
        doc = self.upload("private.txt", b"private evidence")
        self.assertEqual(self.client.post(f"/api/documents/{doc.pk}/extract/").status_code, 200)
        self.client.force_authenticate(self.bob)
        self.assertEqual(self.client.post(f"/api/documents/{doc.pk}/extract/").status_code, 404)
        self.assertEqual(self.client.get(f"/api/documents/{doc.pk}/pages/").status_code, 404)

    def test_failure_keeps_previous_page_data(self):
        doc = self.upload("private.txt", b"original text")
        extract_document(doc)
        with patch("core.extraction._extract_pages", side_effect=ExtractionError("Unprocessable")):
            response = self.client.post(f"/api/documents/{doc.pk}/extract/")
        self.assertEqual(response.status_code, 422)
        doc.refresh_from_db()
        self.assertEqual(doc.processing_status, Document.Status.FAILED)
        self.assertEqual(doc.pages.first().extracted_text, "original text")

    def test_no_leak_of_private_storage_path(self):
        doc = self.upload("private.txt", b"private evidence")
        response = self.client.post(f"/api/documents/{doc.pk}/extract/")
        self.assertNotIn("private_documents", response.content.decode())
        self.assertNotIn(str(Path(self.temp_dir.name)), response.content.decode())
