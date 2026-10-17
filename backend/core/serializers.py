from rest_framework import serializers
from .models import Document, DocumentPage, ExtractedRecord, QuestionAnswer


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["id", "title", "file_type", "original_filename", "processing_status", "uploaded_at"]
        read_only_fields = ["id", "processing_status", "uploaded_at"]

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Title cannot be empty")
        return value

    def validate_file_type(self, value):
        if value.lower() not in ("pdf", "txt"):
            raise serializers.ValidationError("Only PDF and TXT metadata types are supported")
        return value.lower()


class DocumentPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentPage
        fields = ["id", "page_number", "extracted_text"]


class ExtractedRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtractedRecord
        fields = ["id", "record_type", "extracted_data", "validation_status", "created_at"]


class QuestionAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionAnswer
        fields = ["id", "question", "answer", "source_references", "created_at"]
