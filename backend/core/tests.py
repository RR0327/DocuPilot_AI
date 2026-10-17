from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from .models import Document, DocumentPage, ExtractedRecord, QuestionAnswer


class HealthEndpointTests(TestCase):
    def test_health_returns_expected_payload(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "service": "docupilot-api", "phase": "0.1"})

    def test_health_rejects_post(self):
        self.assertEqual(self.client.post(reverse("health")).status_code, 405)


class DocumentApiTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.alice = User.objects.create_user(username="alice", password="password-test-1")
        self.bob = User.objects.create_user(username="bob", password="password-test-2")
        self.client = APIClient()

    def test_anonymous_cannot_list_or_create(self):
        self.assertIn(self.client.get("/api/documents/").status_code, [401, 403])
        self.assertIn(self.client.post("/api/documents/", {"title": "Invoice"}).status_code, [401, 403])

    def test_owner_can_create_and_list_metadata(self):
        self.client.force_authenticate(self.alice)
        created = self.client.post("/api/documents/", {"title": " Invoice 01 ", "file_type": "PDF"})
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()["title"], "Invoice 01")
        self.assertEqual(created.json()["processing_status"], "pending")
        self.assertEqual(self.client.get("/api/documents/").json()["count"], 1)

    def test_owner_isolation_and_nested_resource_protection(self):
        doc = Document.objects.create(owner=self.alice, title="Private")
        DocumentPage.objects.create(document=doc, page_number=1, extracted_text="private text")
        ExtractedRecord.objects.create(document=doc, record_type="invoice", extracted_data={"total": 123})
        self.client.force_authenticate(self.bob)
        self.assertEqual(self.client.get("/api/documents/").json()["count"], 0)
        for url in [f"/api/documents/{doc.pk}/", f"/api/documents/{doc.pk}/pages/", f"/api/documents/{doc.pk}/records/"]:
            self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(f"/api/documents/{doc.pk}/extract/").status_code, 404)

    def test_rejects_invalid_payload_and_read_only_status(self):
        self.client.force_authenticate(self.alice)
        for data in [{"title": "   "}, {"title": "Test", "file_type": "exe"}]:
            self.assertEqual(self.client.post("/api/documents/", data).status_code, 400)
        response = self.client.post("/api/documents/", {"title": "Safe", "processing_status": "completed"})
        self.assertEqual(response.json()["processing_status"], "pending")

    def test_not_implemented_endpoints_do_not_fake_success(self):
        self.client.force_authenticate(self.alice)
        doc = Document.objects.create(owner=self.alice, title="Invoice")
        self.assertEqual(self.client.post("/api/ask/").status_code, 501)
        self.assertEqual(self.client.post(f"/api/documents/{doc.pk}/extract/").status_code, 422)

    def test_metadata_can_be_deleted_but_not_patched(self):
        self.client.force_authenticate(self.alice)
        doc = Document.objects.create(owner=self.alice, title="Invoice")
        self.assertEqual(self.client.delete(f"/api/documents/{doc.pk}/").status_code, 204)
        self.assertEqual(self.client.patch(f"/api/documents/{doc.pk}/", {"title": "Changed"}).status_code, 405)


class DatabaseModelTests(TestCase):
    def test_page_uniqueness_and_cascade(self):
        user = get_user_model().objects.create_user(username="tester")
        doc = Document.objects.create(owner=user, title="Contract")
        DocumentPage.objects.create(document=doc, page_number=1)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                DocumentPage.objects.create(document=doc, page_number=1)
        QuestionAnswer.objects.create(owner=user, question="What?", answer="Insufficient evidence", source_references=[])
        doc.delete()
        self.assertEqual(DocumentPage.objects.count(), 0)
        self.assertEqual(QuestionAnswer.objects.count(), 1)
