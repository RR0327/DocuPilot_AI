from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .extraction import ExtractionError, extract_document
from .invoice_extraction import InvoiceError, extract_invoice
from .models import Document, ExtractedRecord
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
    return Response({"detail": "Evidence-grounded Q&A is scheduled for Phase 1."}, status=status.HTTP_501_NOT_IMPLEMENTED)


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
