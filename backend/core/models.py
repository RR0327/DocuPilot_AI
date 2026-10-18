from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
import uuid


def private_document_path(instance, filename):
    """Unpredictable per-owner storage key; no user-supplied path components."""
    extension = filename.rsplit(".", 1)[-1].lower()
    return f"private_documents/{instance.owner_id}/{uuid.uuid4().hex}.{extension}"


class Document(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to=private_document_path, blank=True, max_length=512)
    file_type = models.CharField(max_length=20, default="pdf")
    original_filename = models.CharField(max_length=255, blank=True)
    processing_status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at", "-id"]

    def __str__(self):
        return self.title


class DocumentPage(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="pages")
    page_number = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    extracted_text = models.TextField(blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["document", "page_number"], name="unique_document_page")]
        ordering = ["page_number"]


class ExtractedRecord(models.Model):
    class ValidationStatus(models.TextChoices):
        UNREVIEWED = "unreviewed", "Unreviewed"
        VALID = "valid", "Valid"
        INVALID = "invalid", "Invalid"

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="extracted_records")
    record_type = models.CharField(max_length=50)
    extracted_data = models.JSONField(default=dict)
    validation_status = models.CharField(max_length=20, choices=ValidationStatus.choices, default=ValidationStatus.UNREVIEWED)
    created_at = models.DateTimeField(auto_now_add=True)


class QuestionAnswer(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="questions")
    question = models.TextField()
    answer = models.TextField()
    source_references = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)


class DocumentChunk(models.Model):
    """Exact page-text slice indexed for deterministic owner-scoped retrieval."""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chunks")
    page_number = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    chunk_index = models.PositiveIntegerField()
    start_offset = models.PositiveIntegerField()
    end_offset = models.PositiveIntegerField()
    content = models.TextField()

    class Meta:
        ordering = ["document_id", "page_number", "chunk_index"]
        constraints = [models.UniqueConstraint(fields=["document", "page_number", "chunk_index"], name="unique_document_chunk")]
        indexes = [models.Index(fields=["document", "page_number"], name="chunk_doc_page_idx")]


class InvoicePaymentState(models.Model):
    """User-entered payment state; never inferred from extraction or due dates."""
    class State(models.TextChoices):
        UNKNOWN = "unknown", "Unknown"
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        DISPUTED = "disputed", "Disputed"

    record = models.OneToOneField(ExtractedRecord, on_delete=models.CASCADE, related_name="payment_state")
    status = models.CharField(max_length=12, choices=State.choices, default=State.UNKNOWN)
    updated_at = models.DateTimeField(auto_now=True)


class ChunkEmbedding(models.Model):
    """Locally computed numeric vectors; cascade deletion on chunk rebuild."""
    chunk = models.ForeignKey(DocumentChunk, on_delete=models.CASCADE, related_name="embeddings")
    model_name = models.CharField(max_length=200)
    vector = models.JSONField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["chunk", "model_name"], name="unique_chunk_embedding_model")]


class InvoiceLineItem(models.Model):
    """Conservatively extracted row with page evidence; not a verified accounting entry."""
    record = models.ForeignKey(ExtractedRecord, on_delete=models.CASCADE, related_name="line_items")
    line_number = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    unit_price = models.DecimalField(max_digits=16, decimal_places=2)
    line_total = models.DecimalField(max_digits=16, decimal_places=2)
    calculated_total = models.DecimalField(max_digits=16, decimal_places=2)
    validation_status = models.CharField(max_length=12, choices=[("matched", "Matched"), ("mismatch", "Mismatch")])
    page_number = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    source_excerpt = models.CharField(max_length=500)

    class Meta:
        ordering = ["record_id", "line_number"]
        constraints = [models.UniqueConstraint(fields=["record", "line_number"], name="unique_invoice_line_number")]


class ExtractionReview(models.Model):
    """Append-only evidence-preserving human decision for an extracted invoice."""
    record = models.ForeignKey(ExtractedRecord, on_delete=models.CASCADE, related_name="reviews")
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="extraction_reviews")
    action = models.CharField(max_length=12, choices=[("approve", "Approve"), ("reject", "Reject"), ("reopen", "Reopen")])
    previous_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    corrections = models.JSONField(default=dict)
    note = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-reviewed_at", "-id"]
