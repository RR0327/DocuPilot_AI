from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Document(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=255)
    # File upload is intentionally postponed until Phase 1; no arbitrary path is exposed.
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
