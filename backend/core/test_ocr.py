"""Deterministic OCR regressions; no Tesseract executable needed for unit tests."""
import io
import tempfile
from unittest.mock import patch

import fitz
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from .models import Document, DocumentPage, DocumentChunk
from .ocr import OCRError

class OCRWorkflowTests(TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        settings = override_settings(MEDIA_ROOT=folder.name)
        settings.enable()
        self.addCleanup(settings.disable)
        User = get_user_model()
        self.alice = User.objects.create_user(username="ocr-alice", password="pass")
        self.bob = User.objects.create_user(username="ocr-bob", password="pass")
        self.client = APIClient()
        self.client.force_authenticate(self.alice)

    def image(self, fmt="PNG"):
        stream = io.BytesIO()
        Image.new("RGB", (200, 80), "white").save(stream, format=fmt)
        return stream.getvalue()

    def upload(self, name, raw):
        response = self.client.post("/api/documents/upload/", {"file": SimpleUploadedFile(name, raw)}, format="multipart")
        self.assertEqual(response.status_code, 201, response.content)
        return response.json()["id"]

    def test_png_ocr_index_and_repeat(self):
        doc_id = self.upload("scan.png", self.image())
        with patch("core.ocr._recognize", return_value="Invoice number ZX200 due next month"):
            for _ in range(2):
                response = self.client.post(f"/api/documents/{doc_id}/extract/")
                self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(DocumentPage.objects.filter(document_id=doc_id).count(), 1)
        self.assertTrue(DocumentChunk.objects.filter(document_id=doc_id).exists())
        self.assertIn("ZX200", DocumentPage.objects.get(document_id=doc_id).extracted_text)

    def test_jpeg_image_support(self):
        doc_id = self.upload("scan.jpg", self.image("JPEG"))
        with patch("core.ocr._recognize", return_value="Supplier: Example"):
            self.assertEqual(self.client.post(f"/api/documents/{doc_id}/extract/").status_code, 200)

    def test_invalid_images_rejected(self):
        for name, payload in [("fake.png", b"not png"), ("fake.jpg", b"not jpeg"), ("wrong.jpg", self.image())]:
            response = self.client.post("/api/documents/upload/", {"file": SimpleUploadedFile(name, payload)}, format="multipart")
            self.assertEqual(response.status_code, 400, (name, response.content))

    def test_scanned_pdf_ocr_and_page_number(self):
        with fitz.open() as pdf:
            pdf.new_page()
            raw = pdf.tobytes()
        doc_id = self.upload("scan.pdf", raw)
        with patch("core.extraction.ocr_pdf_page", return_value="OCR evidence on page 1"):
            response = self.client.post(f"/api/documents/{doc_id}/extract/")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(DocumentPage.objects.get(document_id=doc_id).page_number, 1)

    def test_text_pdf_bypasses_ocr(self):
        with fitz.open() as pdf:
            page = pdf.new_page()
            page.insert_text((72,72), "Hello text layer")
            raw=pdf.tobytes()
        doc_id = self.upload("text.pdf", raw)
        with patch("core.extraction.ocr_pdf_page", side_effect=AssertionError("unnecessary OCR")):
            self.assertEqual(self.client.post(f"/api/documents/{doc_id}/extract/").status_code, 200)

    def test_missing_engine_error_and_old_page_preserved(self):
        doc_id=self.upload("scan.png", self.image())
        with patch("core.ocr._recognize", side_effect=OCRError("OCR unavailable")):
            response=self.client.post(f"/api/documents/{doc_id}/extract/")
        self.assertEqual(response.status_code, 422)
        self.assertEqual(Document.objects.get(pk=doc_id).processing_status, "failed")
        self.assertFalse(DocumentPage.objects.filter(document_id=doc_id).exists())

    def test_cross_user_ocr_protected(self):
        doc_id=self.upload("scan.png", self.image())
        self.client.force_authenticate(self.bob)
        self.assertEqual(self.client.post(f"/api/documents/{doc_id}/extract/").status_code, 404)
        self.assertEqual(self.client.get(f"/api/documents/{doc_id}/pages/").status_code, 404)
