"""Synchronous, evidence-preserving text extraction for supported documents.

Phase 1 scope: text-based PDFs and UTF-8 TXT. Never execute uploaded files.
"""
from dataclasses import dataclass

import fitz
from django.db import transaction

from .models import Document, DocumentPage, ExtractedRecord
from .search import rebuild_document_chunks


MAX_PDF_PAGES = 500
MAX_PAGE_TEXT_CHARS = 1_000_000


class ExtractionError(Exception):
    """A file cannot be safely processed as a supported text document."""


@dataclass(frozen=True)
class ExtractionSummary:
    document_id: int
    status: str
    page_count: int
    character_count: int


def _extract_pages(document):
    if not document.file:
        raise ExtractionError("Document has no uploaded file")
    if document.file_type == "txt":
        try:
            with document.file.open("rb") as stream:
                raw = stream.read(10 * 1024 * 1024 + 1)
            if len(raw) > 10 * 1024 * 1024:
                raise ExtractionError("TXT file exceeds the 10 MiB limit")
            text = raw.decode("utf-8-sig", errors="strict")
        except (UnicodeError, OSError, ValueError) as exc:
            raise ExtractionError("TXT document could not be decoded as UTF-8") from exc
        if "\x00" in text:
            raise ExtractionError("TXT document contains prohibited NUL bytes")
        if not text.strip():
            raise ExtractionError("Document contains no extractable text")
        # A TXT file is one logical page because it has no physical pagination.
        return [(1, text)]
    if document.file_type != "pdf":
        raise ExtractionError("Unsupported document type")
    try:
        with document.file.open("rb") as stream:
            raw = stream.read(10 * 1024 * 1024 + 1)
        if len(raw) > 10 * 1024 * 1024:
            raise ExtractionError("PDF file exceeds the 10 MiB limit")
        if not raw.startswith(b"%PDF-"):
            raise ExtractionError("Invalid PDF signature")
        pages = []
        with fitz.open(stream=raw, filetype="pdf") as pdf:
            if pdf.needs_pass:
                raise ExtractionError("Password-protected PDFs are not supported")
            if len(pdf) == 0 or len(pdf) > MAX_PDF_PAGES:
                raise ExtractionError("PDF page count is outside supported limits")
            for number, page in enumerate(pdf, start=1):
                content = page.get_text("text", sort=True)
                if len(content) > MAX_PAGE_TEXT_CHARS:
                    raise ExtractionError("A PDF page exceeds the text extraction limit")
                pages.append((number, content))
        if not any(text.strip() for _, text in pages):
            raise ExtractionError("No extractable text found; scanned PDFs require OCR")
        return pages
    except (fitz.FileDataError, fitz.EmptyFileError, fitz.FileNotFoundError, OSError, ValueError) as exc:
        raise ExtractionError("PDF document is corrupt or cannot be opened") from exc


def extract_document(document):
    """Extract and replace pages atomically, preserving the prior pages on failure.

    Retrying a completed document is idempotent (one row per page). A failed
    re-extraction retains the last successful page set and marks status failed.
    """
    if not document.file:
        document.processing_status = Document.Status.FAILED
        document.save(update_fields=["processing_status"])
        raise ExtractionError("Document has no uploaded file")
    document.processing_status = Document.Status.PROCESSING
    document.save(update_fields=["processing_status"])
    try:
        pages = _extract_pages(document)
        with transaction.atomic():
            ExtractedRecord.objects.filter(document=document, record_type="invoice").delete()
            DocumentPage.objects.filter(document=document).delete()
            DocumentPage.objects.bulk_create([
                DocumentPage(document=document, page_number=number, extracted_text=text)
                for number, text in pages
            ])
            rebuild_document_chunks(document)
            document.processing_status = Document.Status.COMPLETED
            document.save(update_fields=["processing_status"])
        return ExtractionSummary(document.id, document.processing_status, len(pages), sum(len(t) for _, t in pages))
    except Exception:
        document.processing_status = Document.Status.FAILED
        document.save(update_fields=["processing_status"])
        raise
