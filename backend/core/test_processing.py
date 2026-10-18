"""Async job security, broker errors, lifecycle and sync-API regressions."""
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from .models import Document, ProcessingJob, DocumentPage
from .processing import queue_document, BrokerUnavailable, ProcessingConflict
from .tasks import perform_job


class ProcessingTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username="owner_job", password="pw1")
        self.other = User.objects.create_user(username="other_job", password="pw2")
        self.document = Document.objects.create(
            owner=self.owner, title="Policy", file_type="txt",
            file=SimpleUploadedFile("policy.txt", b"Return window is thirty days."),
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)

    @override_settings(DOCUPILOT_ASYNC_ENABLED=False)
    def test_disabled_mode_returns_503_and_sync_api_remains_available(self):
        response = self.client.post(f"/api/documents/{self.document.id}/extract-async/")
        self.assertEqual(response.status_code, 503)
        self.assertFalse(ProcessingJob.objects.exists())
        result = self.client.post(f"/api/documents/{self.document.id}/extract/")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(DocumentPage.objects.filter(document=self.document).count(), 1)

    @override_settings(DOCUPILOT_ASYNC_ENABLED=True)
    @patch("core.tasks.extract_document_job.apply_async")
    def test_queue_permissions_duplicate_conflict_and_poll(self, enqueue):
        response = self.client.post(f"/api/documents/{self.document.id}/extract-async/")
        self.assertEqual(response.status_code, 202)
        identifier = response.data["id"]
        self.assertEqual(response.data["state"], "queued")
        enqueue.assert_called_once()
        self.assertEqual(self.client.get(f"/api/processing-jobs/{identifier}/").status_code, 200)
        self.assertEqual(self.client.post(f"/api/documents/{self.document.id}/extract-async/").status_code, 409)
        self.assertEqual(self.client.post(f"/api/documents/{self.document.id}/extract/").status_code, 409)
        self.assertEqual(self.client.post(f"/api/documents/{self.document.id}/invoice/extract/").status_code, 409)
        self.assertEqual(self.client.post(f"/api/processing-jobs/{identifier}/retry/").status_code, 409)
        self.client.force_authenticate(user=self.other)
        self.assertEqual(self.client.get(f"/api/processing-jobs/{identifier}/").status_code, 404)
        self.assertEqual(self.client.post(f"/api/processing-jobs/{identifier}/retry/").status_code, 404)
        self.assertEqual(self.client.post(f"/api/documents/{self.document.id}/extract-async/").status_code, 404)
        self.client.force_authenticate(user=None)
        self.assertIn(self.client.get(f"/api/processing-jobs/{identifier}/").status_code, (401, 403))

    @override_settings(DOCUPILOT_ASYNC_ENABLED=True)
    @patch("core.tasks.extract_document_job.apply_async", side_effect=OSError("private broker details"))
    def test_broker_fail_closed_without_orphan_job(self, enqueue):
        resp = self.client.post(f"/api/documents/{self.document.id}/extract-async/")
        self.assertEqual(resp.status_code, 503)
        self.assertNotIn("private broker", str(resp.data))
        self.assertFalse(ProcessingJob.objects.exists())

    def test_worker_success_is_idempotent(self):
        job = ProcessingJob.objects.create(document=self.document)
        first = perform_job(str(job.pk))
        self.assertEqual(first["state"], "succeeded")
        self.assertEqual(perform_job(str(job.pk))["state"], "succeeded")
        job.refresh_from_db()
        self.assertIsNotNone(job.finished_at)
        self.assertEqual(job.page_count, 1)
        self.assertEqual(DocumentPage.objects.filter(document=self.document).count(), 1)

    def test_worker_failure_records_sanitized_error_and_retry(self):
        job = ProcessingJob.objects.create(document=self.document)
        with patch("core.extraction.extract_document", side_effect=RuntimeError("secret path")):
            self.assertEqual(perform_job(str(job.pk))["state"], "failed")
        job.refresh_from_db()
        self.assertNotIn("secret path", job.error_message)
        self.assertEqual(job.state, "failed")
        with override_settings(DOCUPILOT_ASYNC_ENABLED=True):
            with patch("core.tasks.extract_document_job.apply_async"):
                response = self.client.post(f"/api/processing-jobs/{job.pk}/retry/")
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data["attempt"], 2)
        self.assertNotEqual(response.data["id"], str(job.pk))
