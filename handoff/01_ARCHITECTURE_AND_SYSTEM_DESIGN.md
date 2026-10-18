# Architecture and system design

## Logical components
```text
Browser (React 19 / Vite 6 / Tailwind / Recharts / react-pdf)
   | same-origin /api requests (Vite proxy in local development)
   | Django session cookie + CSRF for writes
   v
Django REST Framework API + auth, throttling, owner-scoped querysets
   |-- private upload, document pages, PDF evidence service
   |-- extraction: PyMuPDF, TXT reader, optional Tesseract OCR
   |-- indexed chunks + optional local multilingual E5 embeddings
   |-- source-grounded keyword / semantic / hybrid Q&A
   |-- invoice extraction, line items, arithmetic checks, human review
   |-- supplier analytics and exports
   |-- deterministic classification, explanations, feedback, evaluation
   |-- processing job state and recovery commands
   v
SQLite3 (`backend/db.sqlite3`) + private files (`backend/private_media/`)
   ^
   | optional worker dispatch
Celery worker <-- Redis broker [only when DOCUPILOT_ASYNC_ENABLED=true]
```

## Runtime trust boundaries
1. **Browser/API:** TLS required in any exposed deployment; session cookie HttpOnly, Secure in production; CSRF token for writes. Do not expose Django development server publicly.
2. **API/database:** `IsAuthenticated` and owner-filtered querysets must apply to metadata, invoices, evidence, classification, review, exports and jobs. Validate using two separate accounts.
3. **API/private files:** never configure public URL/media serving for `private_media`; the PDF endpoint is owner-scoped. PDF highlighting is approximate text-layer matching rather than exact geometric provenance.
4. **Worker/database:** Celery/Redis are optional; worker consumes queued processing job IDs and writes results to SQLite3; synchronous extraction remains available. SQLite has concurrent-writer constraints; avoid unbounded worker concurrency.
5. **Local models:** multilingual E5 embeddings are optional; offline mode requires a prepopulated model cache. Keyword mode is the fallback; semantic/hybrid may return 503 if the model is unavailable.

## Key entities
`Document` → `DocumentPage` (page text) → `DocumentChunk` / `ChunkEmbedding`; `ExtractedRecord` → `InvoiceLineItem` and `ExtractionReview`; `DocumentClassification` → append-only `ClassificationFeedback`; `ProcessingJob` → status, retry/recovery metadata; `AuthenticationFailure` → hashed login throttling keys. All reside in SQLite3, with private originals on disk. Consult `backend/core/models.py` and migration chain for exact field definitions.

## Principal sequences
**Upload/extract:** Session login → POST upload → private file saved → synchronous extract or queued Celery task → pages/chunks/recorded status and classification → owner-only results.

**Ask/evidence:** POST `/api/ask/` with mode keyword/semantic/hybrid → owner-scoped completed chunks → extractive answer + document/page references → authenticated `private-pdf` route when applicable.

**Human review:** owner inspects invoice/classification with original page evidence → records correction/verification → immutable original extraction/classifier evidence retained alongside review history → effective corrected values used for reporting where supported.

**Backup:** scripts/backup_restore.py uses SQLite online backup API → bundles SQLite snapshot plus private media (no `.env`) → SHA-256 and SQLite integrity check → dry run → isolated confirmation-gated restore. Pause uploads/workers to preserve cross-resource consistency.

## Nonfunctional boundaries
Local demo is designed for modest load and single SQLite deployment; do not infer horizontal scaling, HA, live collaboration or guaranteed real-world model quality. Synthetic benchmark accuracy is **not** independent classification accuracy; human owner agreement is not ground truth. No general LLM generation is implemented. Refer to `05_SECURITY_PRIVACY_AND_LIMITATIONS.md` for release gates.
