from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from .models import Document, ProcessingJob
from .processing import classify_stale_job, recover_job, BrokerUnavailable
from .tasks import perform_job


class RecoveryTests(TestCase):
    def setUp(self):
        user = get_user_model()
        self.owner = user.objects.create_user(username="recovery_owner", password="pwd")
        self.other = user.objects.create_user(username="recovery_other", password="pwd")
        self.doc = Document.objects.create(owner=self.owner, title="Dummy", file_type="txt")

    def age(self, job, *, hours=3):
        ProcessingJob.objects.filter(pk=job.pk).update(created_at=timezone.now()-timedelta(hours=hours))
        job.refresh_from_db()

    def test_stale_classification(self):
        job = ProcessingJob.objects.create(document=self.doc)
        self.assertIsNone(classify_stale_job(job))
        self.age(job)
        self.assertEqual(classify_stale_job(job), "queued")

    @patch("core.tasks.extract_document_job.apply_async")
    def test_requeue_and_limit(self, enqueue):
        job = ProcessingJob.objects.create(document=self.doc)
        self.age(job)
        self.assertEqual(recover_job(job), "requeued")
        job.refresh_from_db()
        self.assertEqual(job.recovery_count, 1)
        self.assertEqual(recover_job(job), "requeued")
        self.assertEqual(recover_job(job), "recovery_exhausted")
        job.refresh_from_db()
        self.assertEqual(job.state, "failed")
        self.assertEqual(enqueue.call_count, 2)

    @patch("core.tasks.extract_document_job.apply_async", side_effect=OSError("private redis"))
    def test_broker_error_preserves_queue(self, enqueue):
        job = ProcessingJob.objects.create(document=self.doc)
        self.age(job)
        with self.assertRaises(BrokerUnavailable):
            recover_job(job)
        job.refresh_from_db()
        self.assertEqual(job.state, "queued")
        self.assertEqual(job.recovery_count, 0)

    def test_expired_running_is_failed_not_requeued(self):
        job = ProcessingJob.objects.create(document=self.doc, state="running", started_at=timezone.now()-timedelta(hours=3))
        self.assertEqual(recover_job(job), "marked_failed")
        job.refresh_from_db()
        self.assertEqual(job.state, "failed")

    def test_overview_is_owner_scoped(self):
        ProcessingJob.objects.create(document=self.doc)
        client = APIClient()
        client.force_authenticate(user=self.owner)
        response = client.get("/api/processing-jobs/overview/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["counts"]["queued"], 1)
        client.force_authenticate(user=self.other)
        self.assertEqual(client.get("/api/processing-jobs/overview/").data["active"], 0)
        client.force_authenticate(user=None)
        self.assertIn(client.get("/api/processing-jobs/overview/").status_code, [401, 403])
