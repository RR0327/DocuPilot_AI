from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .extraction import ExtractionError, extract_document
from .invoice_extraction import InvoiceError, extract_invoice
from .models import Document, ExtractedRecord, QuestionAnswer
from .search import MAX_QUERY_LENGTH, retrieve, answer_from_evidence
from .serializers import DocumentSerializer, DocumentPageSerializer, ExtractedRecordSerializer, UploadDocumentSerializer


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok", "service": "docupilot-api", "phase": "0.1"})


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        return Document.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_destroy(self, instance):
        storage, path = instance.file.storage, instance.file.name
        instance.delete()  # cascades page and record metadata
        if path:
            storage.delete(path)

    @action(detail=True, methods=["get"])
    def pages(self, request, pk=None):
        return Response(DocumentPageSerializer(self.get_object().pages.all(), many=True).data)

    @action(detail=True, methods=["get"])
    def records(self, request, pk=None):
        return Response(ExtractedRecordSerializer(self.get_object().extracted_records.all(), many=True).data)

    @action(detail=True, methods=["post"], url_path="invoice/extract")
    def invoice_extract(self, request, pk=None):
        document = self.get_object()
        try:
            record = extract_invoice(document)
        except InvoiceError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        return Response(ExtractedRecordSerializer(record).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def extract(self, request, pk=None):
        self.get_object()
        document = self.get_object()
        try:
            result = extract_document(document)
        except ExtractionError as exc:
            return Response({"detail": str(exc), "processing_status": "failed"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except (OSError, ValueError):
            return Response({"detail": "Document extraction failed", "processing_status": "failed"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        return Response({
            "document_id": result.document_id,
            "processing_status": result.status,
            "page_count": result.page_count,
            "character_count": result.character_count,
        })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload(request):
    serializer = UploadDocumentSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    document = serializer.save()
    return Response(DocumentSerializer(document).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ask(request):
    question = request.data.get("question")
    if not isinstance(question, str) or not question.strip() or len(question) > MAX_QUERY_LENGTH:
        return Response({"question": ["Provide a nonempty question up to 500 characters."]}, status=400)
    document_ids = request.data.get("document_ids", None)
    if document_ids is not None:
        if not isinstance(document_ids, list) or not document_ids or len(document_ids) > 50 or any(
            type(value) is not int or value <= 0 for value in document_ids
        ):
            return Response({"document_ids": ["Provide 1 to 50 positive integer document IDs."]}, status=400)
        allowed_count = Document.objects.filter(owner=request.user, pk__in=set(document_ids)).count()
        if allowed_count != len(set(document_ids)):
            return Response({"detail": "One or more documents are unavailable."}, status=404)
    evidence = retrieve(request.user, question.strip(), document_ids=document_ids)
    sources = [{"document_id": hit.document_id, "document_title": hit.document_title,
                "page_number": hit.page_number, "excerpt": hit.excerpt,
                "chunk_id": hit.chunk_id, "score": hit.score} for hit in evidence]
    answer = answer_from_evidence(evidence)
    entry = QuestionAnswer.objects.create(owner=request.user, question=question.strip(),
                                          answer=answer, source_references=sources)
    return Response({"id": entry.pk, "question": entry.question, "answer": answer,
                     "source_references": sources, "has_evidence": bool(evidence),
                     "answer_type": "extractive" if evidence else "insufficient_evidence"}, status=200)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def invoices(request):
    """List own invoice extraction records; no cross-user access."""
    records = ExtractedRecord.objects.filter(
        document__owner=request.user, record_type="invoice"
    ).select_related("document").order_by("-created_at", "-pk")
    document_id = request.query_params.get("document_id")
    if document_id is not None:
        if not document_id.isdecimal():
            return Response({"detail": "document_id must be a positive integer"}, status=400)
        records = records.filter(document_id=int(document_id))
    return Response([{
        "document_id": record.document_id,
        **ExtractedRecordSerializer(record).data,
    } for record in records[:200]])
