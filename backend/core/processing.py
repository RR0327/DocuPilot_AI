"""Owner-isolated asynchronous job lifecycle with explicit retry semantics."""
from django.conf import settings
from django.db import transaction
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
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None}
