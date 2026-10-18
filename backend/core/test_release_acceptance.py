"""Phase 5 Step 3 permission, session and release gate regression."""
import json
from io import StringIO
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, TestCase, override_settings
from rest_framework.test import APIClient
from .models import Document, DocumentPage, ExtractedRecord
from .management.commands.release_acceptance import assess

class AcceptanceTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username="acceptance-owner", password="SecureAcceptancePassword2026!")
        self.other = User.objects.create_user(username="acceptance-other", password="SecureAcceptancePassword2026!")
        self.doc = Document.objects.create(owner=self.owner, title="do not expose")
        DocumentPage.objects.create(document=self.doc, page_number=1, extracted_text="private evidence")
        self.invoice = ExtractedRecord.objects.create(document=self.doc, record_type="invoice", extracted_data={"supplier":"private"})

    def test_anonymous_api_denied_without_data(self):
        c = APIClient()
        urls = ["/api/documents/", f"/api/documents/{self.doc.pk}/", "/api/invoices/", "/api/reviews/", "/api/invoices/analytics/", "/api/classification/feedback-quality/", "/api/classification/reliability/", "/api/processing-jobs/overview/"]
        for url in urls:
            with self.subTest(url=url):
                response = c.get(url)
                self.assertIn(response.status_code, (401, 403))
                self.assertNotIn("do not expose", str(response.content))
                self.assertNotIn("private evidence", str(response.content))

    def test_other_owner_cannot_get_document_pages_or_invoice(self):
        c = APIClient()
        c.force_authenticate(user=self.other)
        for url in (f"/api/documents/{self.doc.pk}/", f"/api/documents/{self.doc.pk}/pages/", f"/api/documents/{self.doc.pk}/private-pdf/", f"/api/documents/{self.doc.pk}/classification-review/", f"/api/reviews/{self.invoice.pk}/", f"/api/invoices/{self.invoice.pk}/line-items/"):
            with self.subTest(url=url):
                self.assertEqual(c.get(url).status_code, 404)

    def test_csrf_and_logout_invalidate_session(self):
        c = Client(enforce_csrf_checks=True)
        c.get("/api/auth/csrf/")
        payload = json.dumps({"username":"acceptance-owner", "password":"SecureAcceptancePassword2026!"})
        self.assertEqual(c.post("/api/auth/login/", data=payload, content_type="application/json").status_code, 403)
        token = c.cookies['csrftoken'].value
        self.assertEqual(c.post("/api/auth/login/", data=payload, content_type="application/json", HTTP_X_CSRFTOKEN=token).status_code, 200)
        self.assertEqual(c.get("/api/auth/me/").status_code, 200)
        self.assertEqual(c.post("/api/auth/logout/", HTTP_X_CSRFTOKEN=c.cookies['csrftoken'].value).status_code, 200)
        self.assertIn(c.get(f"/api/documents/{self.doc.pk}/").status_code, (401, 403))

    def test_security_assessment_does_not_expose_secrets(self):
        result = assess()
        self.assertTrue(result['database_engine']['passed'])
        self.assertTrue(result['private_media']['passed'])
        self.assertTrue(result['csrf_middleware']['passed'])
        self.assertNotIn("SECRET_KEY", str(result))
        self.assertNotIn("do not expose", str(result))

    def test_production_gate_rejects_bad_cookies(self):
        with override_settings(DEBUG=False, SESSION_COOKIE_SECURE=False, CSRF_COOKIE_SECURE=False):
            self.assertFalse(assess()['https_and_cookies']['passed'])

    def test_release_command_generates_local_report(self):
        out = StringIO()
        with override_settings(DEBUG=True):
            call_command('release_acceptance', stdout=out)
        report = json.loads(out.getvalue())
        self.assertTrue(report['passed'])
        self.assertEqual(report['phase'], '5.3')
