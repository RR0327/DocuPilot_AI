from rest_framework import serializers
from .ocr import OCRError, validate_image
from .models import Document, DocumentPage, ExtractedRecord, QuestionAnswer, InvoiceLineItem

MAX_DOCUMENT_BYTES = 10 * 1024 * 1024


def validated_document_file(value):
    """Validate actual bytes, not attacker-controlled extension or content type."""
    name = str(value.name).replace("\\", "/").split("/")[-1]
    suffix = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if suffix not in ("pdf", "txt", "png", "jpg", "jpeg"):
        raise serializers.ValidationError("Only PDF, TXT, PNG and JPEG files are allowed")
    if value.size == 0 or value.size > MAX_DOCUMENT_BYTES:
        raise serializers.ValidationError("File must be between 1 byte and 10 MiB")
    position = value.tell()
    try:
        value.seek(0)
        if suffix == "pdf":
            if not value.read(5) == b"%PDF-":
                raise serializers.ValidationError("Invalid PDF signature")
        elif suffix in ("png", "jpg", "jpeg"):
            try:
                validate_image(value.read(), "png" if suffix == "png" else "jpeg")
            except OCRError as exc:
                raise serializers.ValidationError(str(exc)) from exc
        else:
            try:
                text = value.read().decode("utf-8", errors="strict")
                if "\x00" in text:
                    raise serializers.ValidationError("TXT files cannot contain NUL bytes")
            except UnicodeDecodeError:
                raise serializers.ValidationError("TXT file must contain valid UTF-8")
    finally:
        value.seek(position)
    return suffix, name[:255]


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["id", "title", "file_type", "original_filename", "processing_status", "uploaded_at", "has_file", "classification_category"]
        read_only_fields = ["id", "processing_status", "uploaded_at", "has_file", "original_filename", "classification_category"]

    has_file = serializers.SerializerMethodField()
    classification_category = serializers.SerializerMethodField()

    def get_classification_category(self, obj):
        from .models import DocumentClassification
        try:
            return obj.classification.category
        except DocumentClassification.DoesNotExist:
            return None


    def get_has_file(self, obj):
        return bool(obj.file)

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Title cannot be empty")
        return value

    def validate_file_type(self, value):
        if value.lower() not in ("pdf", "txt", "png", "jpg", "jpeg"):
            raise serializers.ValidationError("Only PDF, TXT, PNG and JPEG metadata types are supported")
        return value.lower()


class UploadDocumentSerializer(serializers.Serializer):
    file = serializers.FileField()
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate_file(self, value):
        suffix, filename = validated_document_file(value)
        self.context["validated_suffix"] = suffix
        self.context["validated_filename"] = filename
        return value

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Title cannot be empty")
        return value

    def create(self, validated_data):
        file = validated_data["file"]
        filename = self.context["validated_filename"]
        return Document.objects.create(
            owner=self.context["request"].user,
            title=validated_data.get("title") or filename,
            file_type=self.context["validated_suffix"],
            original_filename=filename,
            file=file,
        )


class DocumentPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentPage
        fields = ["id", "page_number", "extracted_text"]


class InvoiceLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceLineItem
        fields = ["line_number", "description", "quantity", "unit_price", "line_total", "calculated_total", "validation_status", "page_number", "source_excerpt"]


class ExtractedRecordSerializer(serializers.ModelSerializer):
    line_items = InvoiceLineItemSerializer(many=True, read_only=True)
    class Meta:
        model = ExtractedRecord
        fields = ["id", "record_type", "extracted_data", "validation_status", "created_at", "line_items"]


class QuestionAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionAnswer
        fields = ["id", "question", "answer", "source_references", "created_at"]
