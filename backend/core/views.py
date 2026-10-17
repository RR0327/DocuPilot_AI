from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import Document
from .serializers import DocumentSerializer, DocumentPageSerializer, ExtractedRecordSerializer


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    # Preserve the Phase 0 Step 1 response for existing clients and tests.
    return Response({"status": "ok", "service": "docupilot-api", "phase": "0.1"})


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        return Document.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["get"])
    def pages(self, request, pk=None):
        document = self.get_object()
        return Response(DocumentPageSerializer(document.pages.all(), many=True).data)

    @action(detail=True, methods=["get"])
    def records(self, request, pk=None):
        document = self.get_object()
        return Response(ExtractedRecordSerializer(document.extracted_records.all(), many=True).data)

    @action(detail=True, methods=["post"])
    def extract(self, request, pk=None):
        self.get_object()  # authorization and existence check
        return Response({"detail": "Extraction is scheduled for Phase 1."}, status=status.HTTP_501_NOT_IMPLEMENTED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload(request):
    return Response({"detail": "File upload is scheduled for Phase 1."}, status=status.HTTP_501_NOT_IMPLEMENTED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ask(request):
    return Response({"detail": "Evidence-grounded Q&A is scheduled for Phase 1."}, status=status.HTTP_501_NOT_IMPLEMENTED)
