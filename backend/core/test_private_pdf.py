import tempfile
from pathlib import Path
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from .models import Document

class PrivatePdfTests(TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        config = override_settings(MEDIA_ROOT=folder.name)
        config.enable()
        self.addCleanup(config.disable)
        User = get_user_model()
        self.alice = User.objects.create_user(username="pdf-alice", password="pass123")
        self.bob = User.objects.create_user(username="pdf-bob", password="pass123")
        self.client = APIClient()
        self.pdf = Document.objects.create(owner=self.alice, title="Example PDF", file_type="pdf", file=SimpleUploadedFile("sample.pdf", b"%PDF-1.4\nmock sample"))

    def test_owner_can_stream_pdf_without_public_storage_path(self):
        self.client.force_authenticate(self.alice)
        response = self.client.get(f"/api/documents/{self.pdf.pk}/private-pdf/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("no-store", response["Cache-Control"])
        self.assertNotIn("private_documents", response.get("Content-Disposition", ""))
        self.assertTrue(b"".join(response.streaming_content).startswith(b"%PDF-"))

    def test_other_user_and_anonymous_denied(self):
        path = f"/api/documents/{self.pdf.pk}/private-pdf/"
        self.assertIn(self.client.get(path).status_code, (401, 403))
        self.client.force_authenticate(self.bob)
        self.assertEqual(self.client.get(path).status_code, 404)

    def test_non_pdf_missing_file_and_bad_signature(self):
        self.client.force_authenticate(self.alice)
        self.pdf.file_type = "txt"
        self.pdf.save(update_fields=["file_type"])
        self.assertEqual(self.client.get(f"/api/documents/{self.pdf.pk}/private-pdf/").status_code, 415)
        self.pdf.file_type = "pdf"
        self.pdf.file.save("wrong.pdf", SimpleUploadedFile("wrong.pdf", b"not-a-pdf"), save=True)
        self.assertEqual(self.client.get(f"/api/documents/{self.pdf.pk}/private-pdf/").status_code, 422)
        self.pdf.file.delete(save=False)
        self.assertEqual(self.client.get(f"/api/documents/{self.pdf.pk}/private-pdf/").status_code, 404)
