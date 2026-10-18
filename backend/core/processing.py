"""Owner-isolated asynchronous job lifecycle with explicit retry semantics."""
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from .models import ProcessingJob


class BrokerUnavailable(Exception):
    pass


class ProcessingConflict(Exception):
    pass


def queue_document(document, retry_job=None):
    if not settings.DOCUPILOT_ASYNC_ENABLED:
        raise BrokerUnavailable("Background processing is disabled. Use synchronous extraction.")
    from .tasks import extract_document_job
    from .models import Document
    # SQLite writes are serialized; no second active job is allowed for a document.
    with transaction.atomic():
        Document.objects.select_for_update().get(pk=document.pk)
        active = ProcessingJob.objects.filter(document=document, state__in=["queued", "running"]).exists()
        if active:
            raise ProcessingConflict("Document already has an active extraction job")
        attempt = retry_job.attempt + 1 if retry_job else 1
        job = ProcessingJob.objects.create(document=document, attempt=attempt)
        try:
            # Enqueue inside transaction to fail closed on broker errors; task may be
            # picked up immediately, but its first SQLite read waits until commit.
            extract_document_job.apply_async(args=[str(job.pk)], task_id=str(job.pk), retry=False)
        except Exception as exc:
            raise BrokerUnavailable("Redis broker unavailable; use synchronous extraction.") from exc
    return job


def job_payload(job):
    return {"id": str(job.id), "document_id": job.document_id,
            "state": job.state, "attempt": job.attempt,
            "page_count": job.page_count, "character_count": job.character_count,
            "error_message": job.error_message,
            "recovery_count": job.recovery_count,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None}


# Conservative recovery: running jobs are NOT automatically requeued because
# a long OCR task may still be active. Operators explicitly mark timed-out
# jobs as failed, then owners may use the existing retry endpoint.
def classify_stale_job(job, now=None, queued_minutes=30, running_minutes=120):
    now = now or timezone.now()
    if job.state == ProcessingJob.State.QUEUED and job.created_at <= now - timedelta(minutes=queued_minutes):
        return "queued"
    if job.state == ProcessingJob.State.RUNNING and job.started_at and job.started_at <= now - timedelta(minutes=running_minutes):
        return "running"
    return None


def recover_job(job, *, now=None, queued_minutes=30, running_minutes=120, max_requeues=2):
    """Operator-triggered recovery. Returns action; does not leak broker errors."""
    now = now or timezone.now()
    from .tasks import extract_document_job
    with transaction.atomic():
        locked = ProcessingJob.objects.select_for_update().get(pk=job.pk)
        category = classify_stale_job(locked, now, queued_minutes, running_minutes)
        if category is None:
            return "not_stale"
        if category == "running":
            # Never schedule a second worker while the previous may still run.
            locked.state = ProcessingJob.State.FAILED
            locked.error_message = "Worker did not finish within the configured timeout. Review worker status before retrying."
            locked.finished_at = now
            locked.last_recovery_at = now
            locked.save(update_fields=["state", "error_message", "finished_at", "last_recovery_at"])
            return "marked_failed"
        if locked.recovery_count >= max_requeues:
            locked.state = ProcessingJob.State.FAILED
            locked.finished_at = now
            locked.error_message = "Queue recovery limit reached. Retry manually after checking the worker."
            locked.save(update_fields=["state", "finished_at", "error_message"])
            return "recovery_exhausted"
        # Dispatch before recording recovery; failed dispatch leaves prior state
        # unchanged. Reusing task_id is safe because worker checks queued state.
        try:
            extract_document_job.apply_async(args=[str(locked.pk)], task_id=str(locked.pk), retry=False)
        except Exception as exc:
            raise BrokerUnavailable("Redis broker unavailable; queued job remains unchanged.") from exc
        locked.recovery_count += 1
        locked.last_recovery_at = now
        locked.save(update_fields=["recovery_count", "last_recovery_at"])
        return "requeued"
