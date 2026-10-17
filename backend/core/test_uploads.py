import tempfile
from pathlib import Path
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from .models import Document, DocumentPage, ExtractedRecord


class PrivateUploadTests(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.settings_override = override_settings(MEDIA_ROOT=self.tmp.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        User = get_user_model()
        self.alice = User.objects.create_user(username="upload-alice", password="testpass")
        self.bob = User.objects.create_user(username="upload-bob", password="testpass")
        self.client = APIClient()

    def _upload(self, name="invoice.pdf", content=b"%PDF-1.4\nexample", title="Example"):
        return self.client.post("/api/documents/upload/", {"file": SimpleUploadedFile(name, content), "title": title}, format="multipart")

    def test_anonymous_upload_forbidden(self):
        self.assertIn(self._upload().status_code, (401, 403))
        self.assertEqual(Document.objects.count(), 0)

    def test_valid_pdf_private_path_list_and_delete(self):
        self.client.force_authenticate(self.alice)
        response = self._upload()
        self.assertEqual(response.status_code, 201, response.content)
        doc = Document.objects.get()
        self.assertEqual(doc.owner, self.alice)
        self.assertEqual(doc.file_type, "pdf")
        self.assertTrue(doc.file.name.startswith(f"private_documents/{self.alice.pk}/"))
        self.assertNotIn("file", response.json())
        self.assertNotIn("private_documents", str(response.json()))
        self.assertEqual(self.client.get("/api/documents/").json()["count"], 1)
        DocumentPage.objects.create(document=doc, page_number=1)
        ExtractedRecord.objects.create(document=doc, record_type="invoice")
        saved_file = Path(doc.file.path)
        self.assertTrue(saved_file.is_file())
        self.assertEqual(self.client.delete(f"/api/documents/{doc.id}/").status_code, 204)
        self.assertFalse(saved_file.exists())
        self.assertFalse(DocumentPage.objects.exists())
        self.assertFalse(ExtractedRecord.objects.exists())

    def test_txt_valid_and_reject_invalid(self):
        self.client.force_authenticate(self.alice)
        self.assertEqual(self._upload("notes.txt", "Hello বাংলা".encode()).status_code, 201)
        for name, data in [("malware.exe", b"evil"), ("fake.pdf", b"not a pdf"), ("bad.txt", b"\xff"), ("zero.txt", b""), ("null.txt", b"a\x00b")]:
            response = self._upload(name, data)
            self.assertEqual(response.status_code, 400, (name, response.content))
        self.assertEqual(Document.objects.count(), 1)

    def test_size_limit(self):
        self.client.force_authenticate(self.alice)
        self.assertEqual(self._upload("large.pdf", b"%PDF-" + b"x" * (10 * 1024 * 1024)).status_code, 400)

    def test_cross_user_isolation_and_no_delete(self):
        self.client.force_authenticate(self.alice)
        response = self._upload()
        doc = Document.objects.get(pk=response.json()["id"])
        path = Path(doc.file.path)
        self.client.force_authenticate(self.bob)
        self.assertEqual(self.client.get("/api/documents/").json()["count"], 0)
        self.assertEqual(self.client.get(f"/api/documents/{doc.id}/").status_code, 404)
        self.assertEqual(self.client.delete(f"/api/documents/{doc.id}/").status_code, 404)
        self.assertEqual(self.client.get(f"/api/documents/{doc.id}/pages/").status_code, 404)
        self.assertTrue(path.exists())

    def test_existing_metadata_creation_still_works(self):
        self.client.force_authenticate(self.alice)
        self.assertEqual(self.client.post("/api/documents/", {"title": "Legacy", "file_type": "PDF"}).status_code, 201)
