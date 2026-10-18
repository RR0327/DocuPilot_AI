from rest_framework import status, viewsets
from django.http import HttpResponse, FileResponse, Http404
from django.shortcuts import get_object_or_404
from .invoice_dashboard import dashboard, export_csv, filtered_invoices
from rest_framework.decorators import api_view, permission_classes, action, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .extraction import ExtractionError, extract_document
from .models import ProcessingJob
from .processing import queue_document, job_payload, BrokerUnavailable, ProcessingConflict
from .invoice_extraction import InvoiceError, extract_invoice
from .models import Document, ExtractedRecord, QuestionAnswer, InvoicePaymentState
from .review import apply_review, review_details, quality_flags
from .search import MAX_QUERY_LENGTH, retrieve, answer_from_evidence
from .semantic import SemanticUnavailable
from .serializers import DocumentSerializer, DocumentPageSerializer, ExtractedRecordSerializer, UploadDocumentSerializer, InvoiceLineItemSerializer


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

    @action(detail=True, methods=["get"], url_path="private-pdf")
    def private_pdf(self, request, pk=None):
        """Stream a PDF exclusively to its authenticated owner, never via public MEDIA_URL."""
        document = self.get_object()
        if document.file_type.lower() != "pdf" or not document.file:
            return Response({"detail": "PDF preview is available only for uploaded PDFs."}, status=415)
        try:
            handle = document.file.open("rb")
            if handle.read(5) != b"%PDF-":
                handle.close()
                return Response({"detail": "Invalid PDF signature."}, status=422)
            handle.seek(0)
        except (OSError, ValueError, FileNotFoundError):
            raise Http404("PDF is unavailable")
        response = FileResponse(handle, content_type="application/pdf", as_attachment=False)
        response["Cache-Control"] = "private, no-store, max-age=0"
        response["X-Content-Type-Options"] = "nosniff"
        response["Content-Security-Policy"] = "default-src 'none'; sandbox"
        response["Content-Disposition"] = 'inline; filename="document.pdf"'
        return response

    @action(detail=True, methods=["get"])
    def pages(self, request, pk=None):
        return Response(DocumentPageSerializer(self.get_object().pages.all(), many=True).data)

    @action(detail=True, methods=["get"])
    def records(self, request, pk=None):
        return Response(ExtractedRecordSerializer(self.get_object().extracted_records.all(), many=True).data)

    @action(detail=True, methods=["post"], url_path="invoice/extract")
    def invoice_extract(self, request, pk=None):
        document = self.get_object()
        if ProcessingJob.objects.filter(document=document, state__in=["queued", "running"]).exists():
            return Response({"detail": "Background extraction is active; try again when it finishes."}, status=409)
        try:
            record = extract_invoice(document)
        except InvoiceError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        return Response(ExtractedRecordSerializer(record).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="extract-async")
    def extract_async(self, request, pk=None):
        document = self.get_object()
        if not document.file:
            return Response({"detail": "Document has no uploaded file"}, status=422)
        try:
            job = queue_document(document)
        except BrokerUnavailable as exc:
            return Response({"detail": str(exc)}, status=503)
        except ProcessingConflict as exc:
            return Response({"detail": str(exc)}, status=409)
        response = Response(job_payload(job), status=202)
        response["Cache-Control"] = "no-store"
        return response

    @action(detail=True, methods=["post"])
    def extract(self, request, pk=None):
        document = self.get_object()
        if ProcessingJob.objects.filter(document=document, state__in=["queued", "running"]).exists():
            return Response({"detail": "Background extraction is active; try again when it finishes."}, status=409)
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
    mode = request.data.get("mode", "keyword")
    if mode not in ("keyword", "semantic", "hybrid"):
        return Response({"mode": ["Choose keyword, semantic or hybrid."]}, status=400)
    try:
        evidence = retrieve(request.user, question.strip(), document_ids=document_ids, mode=mode)
    except SemanticUnavailable as exc:
        return Response({"detail": str(exc), "mode": mode}, status=503)
    sources = [{"document_id": hit.document_id, "document_title": hit.document_title,
                "page_number": hit.page_number, "excerpt": hit.excerpt,
                "chunk_id": hit.chunk_id, "score": hit.score, "retrieval_method": hit.retrieval_method} for hit in evidence]
    answer = answer_from_evidence(evidence)
    entry = QuestionAnswer.objects.create(owner=request.user, question=question.strip(),
                                          answer=answer, source_references=sources)
    return Response({"id": entry.pk, "question": entry.question, "answer": answer,
                     "source_references": sources, "has_evidence": bool(evidence),
                     "answer_type": "extractive" if evidence else "insufficient_evidence", "retrieval_mode": mode}, status=200)


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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def invoice_analytics(request):
    """Aggregate only the current user's invoice records, with currency isolation."""
    from .supplier_analytics import analytics_for_user
    allowed = {"currency", "year", "limit"}
    if set(request.query_params.keys()) - allowed:
        return Response({"detail": "Unsupported analytics filter."}, status=400)
    try:
        raw_year = request.query_params.get("year")
        raw_limit = request.query_params.get("limit", "10")
        if raw_year is not None and (not raw_year.isdecimal() or len(raw_year) != 4):
            raise ValueError("year must be a four-digit year")
        if not raw_limit.isdecimal():
            raise ValueError("limit must be a positive integer")
        data = analytics_for_user(
            request.user, currency=request.query_params.get("currency") or None,
            year=int(raw_year) if raw_year is not None else None,
            limit=int(raw_limit))
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=400)
    response = Response(data)
    response["Cache-Control"] = "no-store"
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def invoice_dashboard(request):
    return Response(dashboard(request.user))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def invoice_report(request):
    try:
        rows = filtered_invoices(request.user, request.query_params)
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=400)
    return Response({"count": len(rows), "results": rows})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def invoice_export(request):
    try:
        rows = filtered_invoices(request.user, request.query_params)
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=400)
    response = HttpResponse(export_csv(rows), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="docupilot_invoices.csv"'
    response["Cache-Control"] = "no-store"
    return response


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def invoice_payment_status(request, record_id):
    record = get_object_or_404(ExtractedRecord, pk=record_id, record_type="invoice", document__owner=request.user)
    new_status = request.data.get("payment_status")
    if new_status not in InvoicePaymentState.State.values or len(request.data) != 1:
        return Response({"payment_status": ["Use exactly one valid status: unknown, pending, paid or disputed."]}, status=400)
    state, _ = InvoicePaymentState.objects.update_or_create(record=record, defaults={"status": new_status})
    return Response({"record_id": record.pk, "payment_status": state.status, "updated_at": state.updated_at})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def invoice_line_items(request, record_id):
    """Never reveal line items from another user's invoice."""
    record = get_object_or_404(ExtractedRecord, pk=record_id, record_type="invoice", document__owner=request.user)
    items = record.line_items.all().order_by("line_number")
    return Response({"record_id": record.id, "count": items.count(), "results": InvoiceLineItemSerializer(items, many=True).data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def review_queue(request):
    status_filter = request.query_params.get("status", "unreviewed")
    if status_filter not in ("unreviewed", "valid", "invalid", "all"):
        return Response({"status": ["Choose unreviewed, valid, invalid or all."]}, status=400)
    records = ExtractedRecord.objects.filter(record_type="invoice", document__owner=request.user).select_related("document").order_by("-created_at", "-pk")
    if status_filter != "all":
        records = records.filter(validation_status=status_filter)
    rows = []
    for record in records[:200]:
        detail = review_details(record)
        detail.pop("history")
        detail["needs_attention"] = bool(detail["quality_flags"])
        rows.append(detail)
    rows.sort(key=lambda r: (not r["needs_attention"], -r["record_id"]))
    return Response({"count": len(rows), "results": rows})


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def review_record(request, record_id):
    record = get_object_or_404(ExtractedRecord, pk=record_id, record_type="invoice", document__owner=request.user)
    if request.method == "POST":
        from rest_framework.exceptions import ValidationError
        try:
            record = apply_review(record.pk, request.user, request.data)
        except ExtractedRecord.DoesNotExist:
            raise Http404
    return Response(review_details(record))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def processing_job_detail(request, job_id):
    job = get_object_or_404(ProcessingJob, pk=job_id, document__owner=request.user)
    response = Response(job_payload(job))
    response["Cache-Control"] = "no-store"
    return response


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def retry_processing_job(request, job_id):
    prior = get_object_or_404(ProcessingJob, pk=job_id, document__owner=request.user)
    if prior.state != ProcessingJob.State.FAILED:
        return Response({"detail": "Only failed jobs may be retried."}, status=409)
    try:
        job = queue_document(prior.document, retry_job=prior)
    except BrokerUnavailable as exc:
        return Response({"detail": str(exc)}, status=503)
    except ProcessingConflict as exc:
        return Response({"detail": str(exc)}, status=409)
    response = Response(job_payload(job), status=202)
    response["Cache-Control"] = "no-store"
    return response
