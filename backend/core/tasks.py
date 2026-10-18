"""Worker tasks call the same tested extraction pipeline as the sync endpoint."""
from django.db import transaction
from django.utils import timezone
from .models import ProcessingJob, Document

# Import is optional when the broker is disabled; worker installs requirements-async.txt.
try:
    from celery import shared_task
except ImportError:
    def shared_task(*args, **kwargs):
        def decorate(fn):
            return fn
        return decorate


def perform_job(job_id):
    """Run one queued job; duplicate task deliveries cannot run extraction twice."""
    # Atomic state claim prevents duplicate Redis delivery executing twice,
    # including on SQLite where SELECT FOR UPDATE has limited semantics.
    claimed = ProcessingJob.objects.filter(pk=job_id, state=ProcessingJob.State.QUEUED).update(
        state=ProcessingJob.State.RUNNING, started_at=timezone.now()
    )
    if not claimed:
        return {"state": ProcessingJob.objects.get(pk=job_id).state}
    job = ProcessingJob.objects.get(pk=job_id)
    try:
        from .extraction import extract_document
        result = extract_document(Document.objects.get(pk=job.document_id))
    except Exception:
        # Never expose file paths, OCR logs or exception internals in API responses.
        ProcessingJob.objects.filter(pk=job_id, state=ProcessingJob.State.RUNNING).update(
            state=ProcessingJob.State.FAILED,
            error_message="Extraction failed. Check the worker logs for details.",
            finished_at=timezone.now(),
        )
        return {"state": "failed"}
    ProcessingJob.objects.filter(pk=job_id, state=ProcessingJob.State.RUNNING).update(
        state=ProcessingJob.State.SUCCEEDED, page_count=result.page_count,
        character_count=result.character_count, finished_at=timezone.now(), error_message="",
    )
    return {"state": "succeeded", "page_count": result.page_count}


@shared_task(name="docupilot.extract_document", ignore_result=True)
def extract_document_job(job_id):
    return perform_job(job_id)
