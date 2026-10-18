from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.core.management import call_command
from django.core.management.base import CommandError
from io import StringIO
from .models import Document

class ReleaseSecurityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="release-owner", password="test-secret")
        self.other = get_user_model().objects.create_user(username="release-other", password="test-secret")
        self.document = Document.objects.create(owner=self.user, title="Confidential Contract")
        self.client = APIClient()

    def test_anonymous_cannot_access_private_document_or_review(self):
        for url in (f"/api/documents/{self.document.pk}/", f"/api/documents/{self.document.pk}/classification-review/", "/api/classification/feedback-quality/", "/api/processing-jobs/overview/"):
            self.assertIn(self.client.get(url).status_code, (401, 403))

    def test_other_user_cannot_access_document_or_review(self):
        self.client.force_authenticate(self.other)
        for url in (f"/api/documents/{self.document.pk}/", f"/api/documents/{self.document.pk}/classification-review/", f"/api/documents/{self.document.pk}/private-pdf/"):
            self.assertEqual(self.client.get(url).status_code, 404)

    def test_no_public_private_media_route(self):
        from django.conf import settings
        self.assertFalse(getattr(settings, "MEDIA_URL", None))
        self.assertNotIn("corsheaders.middleware.CorsMiddleware", settings.MIDDLEWARE)

    def test_development_gate_reports_warning(self):
        output = StringIO()
        with override_settings(DEBUG=True):
            call_command("release_check", stdout=output)
        self.assertIn("local development", output.getvalue())

    def test_production_gate_rejects_insecure_http(self):
        with override_settings(DEBUG=False, SECURE_SSL_REDIRECT=False, ALLOWED_HOSTS=["localhost"], SECURE_HSTS_SECONDS=0):
            with self.assertRaises(CommandError):
                call_command("release_check", stdout=StringIO())
