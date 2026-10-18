# DocuPilot AI

**Intelligent Document Processing & Knowledge Assistant**  
**Copyright © 2026 Tech_Innovators** · **Phase 2 Step 2 — SQLite Hybrid Retrieval**

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Contributing](https://img.shields.io/badge/Contributing-Guidelines-green.svg)](CONTRIBUTING.md)
[![Security](https://img.shields.io/badge/Security-Policy-orange.svg)](SECURITY.md)

[License](LICENSE) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md)

## Overview

DocuPilot AI is a Django + React document intelligence application. Authorized users can upload private text-based PDF and UTF-8 TXT files, extract page text, parse selected invoice fields, search indexed passages, ask extractive questions with document/page references, and review invoice payment status and due dates. SQLite3 is the default database; **PostgreSQL is not required**.

### Current MVP capabilities

- Django REST Framework backend and React + Vite + Tailwind frontend.
- React sign-in using existing Django username/password and HTTP Basic authentication. **Credentials are held in React memory only** and cleared on sign-out or reload. No persistent tokens or passwords are stored.
- Private owner-isolated PDF/TXT upload, listing, deletion, page extraction, invoice field extraction.
- Document chunk indexing and SQLite-compatible keyword retrieval; extractive answers with supporting document/page excerpts.
- Invoice dashboard with owner-set payment status (`unknown`, `pending`, `paid`, `disputed`), due-date filters, currency-separated pending totals, and CSV export.
- Error, loading and empty states; mobile-responsive frontend; frontend API regression tests and backend Django tests.

**Limitations:** This is a local-development MVP, not a production-secure deployment. HTTP Basic credentials are transmitted in an Authorization header on every request; **never expose this service without TLS/HTTPS and a reviewed authentication model**. Scanned PDFs and PNG/JPEG can use optional Tesseract OCR. Q&A is extractive, not an LLM answer. Financial fields require human verification. The document listing currently shows the first page (20 documents) from Django's paginated API. The React invoice dashboard uses backend APIs rather than direct DB access.

## Technology

| Layer | Stack |
| --- | --- |
| Frontend | React 19, Vite 6, Tailwind CSS 3 |
| Backend | Django, Django REST Framework |
| Database | SQLite3 |
| Extraction | PyMuPDF + deterministic Python rules |
| Search | SQLite-compatible keyword chunks |
| Auth | DRF Basic authentication in the development frontend; session authentication supported by backend |

## Windows 11 quick start

Prerequisites: Python 3.12, Node.js 22 LTS (or a compatible current LTS release), npm, and PowerShell.

**Backend — terminal 1**, from repository root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
cd backend
python manage.py check
python manage.py migrate
python manage.py makemigrations --check --dry-run
python manage.py test --verbosity 2
python manage.py createsuperuser  # only once; skip if you already have an account
python manage.py runserver
```

Preserve existing `.env` and `backend/db.sqlite3` when upgrading. Keep the SQLite database and `backend/private_media` files together when backing up user data.

**Frontend — terminal 2**, from repository root:

```powershell
cd frontend
npm install
npm test
npm run build
npm run dev
```

Open http://localhost:5173, sign in with your Django superuser or other existing account, upload a PDF/TXT, select **Extract text**, then optionally **Extract invoice**, **Ask documents**, or open **Invoice intelligence**. The Vite dev server proxies `/api` to `http://127.0.0.1:8000`, avoiding a separate CORS setup in local development.

For a complete end-to-end verification matrix and troubleshooting, see [PHASE1_STEP6_TESTING.md](PHASE1_STEP6_TESTING.md).

## API endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health/` | Health check |
| POST | `/api/documents/upload/` | Upload PDF or TXT |
| GET | `/api/documents/` | List owned documents (paginated) |
| GET / DELETE | `/api/documents/{id}/` | Document metadata / delete |
| POST | `/api/documents/{id}/extract/` | Extract and index text |
| GET | `/api/documents/{id}/pages/` | Retrieve extracted page text |
| POST | `/api/documents/{id}/invoice/extract/` | Extract invoice fields |
| POST | `/api/ask/` | Evidence-grounded extractive answer |
| GET | `/api/invoices/dashboard/` | Invoice counts and pending balances |
| GET | `/api/invoices/report/` | Filter invoices |
| GET | `/api/invoices/export/` | CSV export |
| PATCH | `/api/invoices/{record_id}/payment-status/` | Set owner-verified payment status |

## Roadmap

| Phase | Scope | Status |
| --- | --- | --- |
| 0 | Foundation, SQLite3 models and migration | Complete |
| 1 | Secure upload, extraction, invoice parsing, keyword Q&A, reporting, React MVP | Step 6 packaged; verify locally |
| 2 | OCR, semantic/hybrid retrieval, highlighted evidence, line items | Planned |
| 3 | Review queue, supplier analytics, async tasks | Planned |
| 4 | Classification, multi-document Q&A, RBAC, audit logs | Planned |
| 5 | Deployment and production readiness review | Planned extension |

## Repository governance

© 2026 **Tech_Innovators**. Released under the [MIT License](LICENSE). See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution practices and [SECURITY.md](SECURITY.md) for vulnerability disclosure. Do not upload sensitive or regulated documents into public demonstration instances.


## Phase 1 Step 7 — MVP verification

Frontend document pagination now loads all owner-scoped pages. Client-side PDF/TXT size and extension checks provide early feedback (backend remains authoritative). The browser E2E contract suite covers authentication, text extraction, source-grounded Q&A and upload validation. See [Phase 1 Step 7 testing](PHASE1_STEP7_TESTING.md).

**Release status:** MVP release candidate for local demonstration only. Production deployment remains blocked pending live E2E, backup restoration, authentication hardening and security checks.


## Phase 2 Step 1 — Local OCR (PDF and images)

Supports scanned PDFs (page-wise fallback to OCR), PNG and JPEG using **Tesseract + pytesseract + Pillow**, with the original PyMuPDF/TXT extraction intact. Files stay private. See [Phase 2 Step 1 Windows 11 testing](PHASE2_STEP1_TESTING.md) for setup, verification and OCR limitations. On Windows install Tesseract separately; set `DOCUPILOT_TESSERACT_CMD` when its executable is not on PATH. Optional Bangla recognition requires `ben.traineddata`. Existing [LICENSE](LICENSE), [CONTRIBUTING.md](CONTRIBUTING.md), and [SECURITY.md](SECURITY.md) links remain active.


## Phase 2 Step 2 — Multilingual semantic and hybrid retrieval

Document evidence search now supports three optional request modes: `keyword` (default, no model required), `semantic` (local multilingual embeddings), and `hybrid` (semantic + keyword using reciprocal rank fusion). All retrieved rows are restricted to the authenticated owner's completed documents and optional explicit document IDs. Source excerpts and page numbers remain unchanged; they are not synthesized answers. The local model is only loaded for semantic or hybrid requests. Cached vectors live in the SQLite `ChunkEmbedding` table and are cascade-deleted when chunks are rebuilt.

To enable semantic search on Windows, install `backend/requirements-semantic.txt` in the backend virtual environment. First inference may download `intfloat/multilingual-e5-small`, which must be available locally for offline mode. The backend returns an explicit 503 when the semantic model is missing; default keyword requests keep working. The use of a local model does not imply perfect Bangla performance.

`POST /api/ask/` accepts an optional `mode` of `keyword`, `semantic`, or `hybrid`; default remains `keyword`. A source reference now includes `retrieval_method`, and the response includes `retrieval_mode`. See [Phase 2 Step 2 Windows testing](PHASE2_STEP2_TESTING.md) for complete instructions and acceptance criteria.


## Phase 2 Step 3 — Private highlighted PDF evidence viewer

For an evidence citation from a PDF, choose **View highlighted PDF**. The backend serves PDFs only through the authenticated, owner-scoped `GET /api/documents/{id}/private-pdf/` endpoint. The file is never served via a public media route or persisted in localStorage. The browser creates and revokes a temporary object URL.

The React viewer uses `react-pdf` (PDF.js) to render the referenced page, navigate pages and mark matching text-layer words. Word highlighting is approximate, **not verified geometric evidence coordinates**. On scanned/OCR-only pages, the source excerpt remains visible alongside the original page; no fabricated overlay is displayed. Text-only and image documents retain the existing page-text interface.

Run `npm install` in `frontend` to install the added `react-pdf` dependency. See [PHASE2_STEP3_TESTING.md](PHASE2_STEP3_TESTING.md).

Limitations: large/complex PDFs may increase memory use; offline PDF.js worker assets must be bundled by Vite. This is a locally demonstrated MVP viewer, not approval for public confidential-document hosting.

## Phase 2 Step 4 — Invoice line items

After processing a document, select **Extract invoice**. Recognized table rows are saved
as `InvoiceLineItem` records linked to their immutable extraction record. In **Invoice
intelligence**, click **Line items** to inspect each row, quantity, unit price, reported
line total, arithmetic validation, and supporting page. The owner-scoped endpoint is
`GET /api/invoices/{record_id}/line-items/`.

The rule-based parser requires an explicit column heading containing description/item,
quantity, unit price, and amount/total; then it recognizes simple, aligned or pipe-
separated rows. Unknown, malformed, non-tabular and complex OCR layouts are **not**
filled with guessed values. A row is `matched` only when the reported amount agrees
with quantity times unit price to a cent; otherwise it is `mismatch`. The entire
invoice remains `unreviewed` until a human verifies it against the original PDF.

This step uses the original SQLite3 database and migration
`core.0006_invoicelineitem`; it does not require PostgreSQL, paid models, or new
frontend dependencies. See [Phase 2 Step 4 testing](PHASE2_STEP4_TESTING.md).

## Phase 2 Step 5 — Evidence and extraction quality evaluation

Adds reproducible local quality metrics using the existing keyword, semantic and hybrid retrieval code paths. The benchmark command (`python manage.py evaluate_docupilot --mode keyword`) creates isolated synthetic documents, measures Recall@5, MRR, no-answer abstention and exact citation provenance, measures invoice exact-field extraction, and rolls back its temporary database records. It also reports *illustrative* OCR character-error rates from supplied reference/prediction text; these are **not live OCR accuracy claims**. Additional review warnings flag due dates preceding invoice dates and recognized line totals inconsistent with a stated subtotal. No source values are modified automatically. The benchmark corpus is a smoke test, not evidence of real-world reliability.

See [Phase 2 Step 5 testing and release gate](PHASE2_STEP5_TESTING.md) for Windows 11 commands and real-data evaluation requirements. SQLite3 and all prior functionality, private storage, and governance documents are preserved. **Phase 2 is only ready for a local demonstration after user-executed acceptance tests; public deployment requires separate security and operations work.**

## Phase 3 Step 1 — Human Review Queue

A new **Human review** React workspace lists the signed-in owner's extracted invoices, prioritizing missing fields, warnings and arithmetic mismatches. Reviewers can approve with validated field corrections, reject with a mandatory reason, or reopen reviewed records. Every decision is retained in an `ExtractionReview` SQLite table, separate from immutable extracted evidence. Approved corrections flow through the existing invoice report, dashboard and CSV; reopening restores unreviewed source values. Review actions are authenticated and scoped to the document owner, not global staff roles.

- `GET /api/reviews/?status=unreviewed|valid|invalid|all` — owner-scoped queue.
- `GET /api/reviews/{record_id}/` — original/effective fields, evidence, flags and history.
- `POST /api/reviews/{record_id}/` — `{ "action": "approve", "corrections": {"total": "250.00"}, "note": "Checked source" }`, or `reject` with a reason, or `reopen`.

See [Phase 3 Step 1 testing instructions](PHASE3_STEP1_TESTING.md). SQLite3 remains the sole database. The repository's [MIT License](LICENSE), [Contributing](CONTRIBUTING.md) and [Security](SECURITY.md) files remain unchanged.

## Phase 3 Step 2 — Supplier invoice analytics

Authenticated `GET /api/invoices/analytics/` supports `currency=BDT|USD|EUR|GBP`, `year=YYYY`, and `limit=1..50`. The response includes currency-specific invoice-value totals, dated monthly trends, top suppliers, excluded-record reasons, and source-value basis metadata. The **Supplier analytics** React navigation item displays Recharts line and bar charts with a currency selector. Approved human-review corrections are used; rejected invoice records are excluded. Values are based on invoice dates, **not confirmed cash payments**. No database migration is necessary.

See [Phase 3 Step 2 testing and acceptance](PHASE3_STEP2_TESTING.md). Existing project links: [License](LICENSE) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md).

## Phase 3 Step 3 — Optional background extraction

DocuPilot AI can now run PDF/OCR extraction in a Celery worker, with Redis as broker and an owner-scoped SQLite3 `ProcessingJob` status record. This is **optional**; the default synchronous `POST /api/documents/{id}/extract/` endpoint continues working when Celery/Redis are absent. Enable with `DOCUPILOT_ASYNC_ENABLED=true` after installing `backend/requirements-async.txt` and running a local Redis broker and worker (`celery -A config worker --pool=solo --concurrency=1 --loglevel=info` on Windows).

The Document workspace offers **Background extract**, job status updates and a retry action for failed jobs. Jobs have queued/running/succeeded/failed states, not percentage-complete telemetry. For exact commands, expected statuses, regression checks and security limitations see [Phase 3 Step 3 testing](PHASE3_STEP3_TESTING.md). No current features require external PostgreSQL or a paid AI API.


## Phase 3 Step 4 — Job recovery and observability

Optional background extraction now includes atomic job claiming, bounded queued-job recovery, operator-only stale running-job remediation, and an authenticated `GET /api/processing-jobs/overview/` summary. The management command defaults to **dry-run**, and `--apply` must only be used after checking the Redis worker. No automatic requeue of running jobs is performed. See [Phase 3 Step 4 testing](PHASE3_STEP4_TESTING.md). SQLite3 remains the database; all existing review, analytics, OCR, retrieval and private PDF features are preserved.

## Phase 4 Step 1 — Explainable Document Classification

After successful synchronous or Celery extraction, DocuPilot AI classifies extracted text as **invoice**, **policy**, **report**, **contract**, or **unknown**. Document owners can view source-page keyword evidence or trigger a reclassification on their own stored pages. Results are persisted in the SQLite3 `DocumentClassification` table (migration `0010_documentclassification`) and exposed using `GET/POST /api/documents/{id}/classification/` and the `classification_category` property in document lists. Category weights indicate matched rules, **not a probabilistic confidence estimate**. Ambiguous or low-evidence documents remain `unknown` for manual inspection. No paid APIs, private-file exposure, or replacement of the original document evidence are introduced.

See [Phase 4 Step 1 test and Windows 11 verification](PHASE4_STEP1_TESTING.md). Project policies: [LICENSE](LICENSE), [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md).

## Phase 4 Step 2 — Classification quality and explainability checks

Phase 4 Step 2 provides a **synthetic classification quality benchmark** (15 labeled examples, including the `unknown` class) with multiclass precision, recall, F1, macro averages, confusion matrix, and evidence-grounding diagnostics. The benchmark is deterministic and does **not** establish accuracy on real uploaded documents.

- Authenticated `GET /api/classification/evaluation/` returns the bundled synthetic benchmark report; it does not read private user documents.
- Open **Classification quality** in the React navigation to inspect class metrics, unknown handling and actual-versus-predicted confusion matrix.
- Run `cd backend; python manage.py evaluate_classification --output classification_report.json` for an offline JSON report.
- Evidence for the selected category is prioritized inside the existing 12-excerpt display cap; stored page text remains authoritative.
- No SQLite3 migrations are required. All existing processing and document-owner restrictions remain in force.

See [PHASE4_STEP2_TESTING.md](PHASE4_STEP2_TESTING.md) for Windows 11 setup, tests, release acceptance and limitations.

## Phase 4 Step 3 — classification refinement

- Adds Bangla invoice/policy/report/contract signals, OCR-tolerant matching and exact source excerpts. Classification remains explainable and can abstain.
- Reports false abstentions, unsafe guesses, and wrong-category errors in synthetic quality reporting.
- Adds optional *externally human-labeled* evaluation CLI (`python manage.py evaluate_classification --dataset evaluation/independent_labels.json`) with provenance metadata. The independently labeled dataset is **not supplied**; refer to `backend/evaluation/independent_labels_TEMPLATE.json`. No real-world accuracy is claimed.
- Full verification instructions: [PHASE4_STEP3_TESTING.md](PHASE4_STEP3_TESTING.md).


## Phase 4 Step 4 — human-verified document classification

Classification decisions are now tracked through an append-only `ClassificationFeedback` history. Machine predictions and their original page-linked evidence remain untouched; a human can verify, override (with a reason), or clear the current human decision. The owner-only `GET/POST /api/documents/{id}/classification-review/` endpoint returns both machine and effective reviewed categories. `GET /api/classification/feedback-evaluation/` summarizes **review activity**, not independent classification accuracy. See [PHASE4_STEP4_TESTING.md](PHASE4_STEP4_TESTING.md) for installation, migration, security and regression procedures.


## Phase 4 Step 5 — Operational classification feedback quality

- Owner-scoped `GET /api/classification/feedback-quality/` returns review coverage, machine-vs-owner agreement/disagreement, and a count of machine classifications that changed after review. This is **not a classifier accuracy estimate**.
- `POST /api/classification/feedback-label-export/` requires `{"confirm_label_only_export": true}` and returns a pseudonymous **label-only** operational feedback snapshot. Each export generates fresh random aliases. No document text, page evidence, filenames, identifiers, reviewer IDs or notes are exported.
- Owner feedback does **not** become independently verified ground truth by virtue of approval. A genuine independent test set still requires consented documents, separate annotators, provenance, and adjudication. Label-only exports cannot be used to re-run the classifier benchmark.
- React navigation provides **Feedback quality** with an agreement table and explicitly confirmed privacy-safe export.
- The APIs require authenticated users and set `Cache-Control: no-store`; the database remains SQLite3, and no migrations are introduced.

See [Phase 4 Step 5 testing](PHASE4_STEP5_TESTING.md) for acceptance instructions.


## Phase 4 Step 6 — reliability and adjudication

See [Phase 4 Step 6 testing guide](PHASE4_STEP6_TESTING.md). An independent two-reviewer and adjudicator dataset can be evaluated offline with `python manage.py evaluate_adjudicated_classification --dataset evaluation/adjudicated_private.json --output adjudicated_report.json`. The template under `backend/evaluation/adjudicated_labels_TEMPLATE.json` is **not** real ground truth. The owner-only `/api/classification/reliability/` endpoint and Reliability React tab show operational errors, not accuracy. No migration is required.

## Phase 5 Step 1 — Integration, security baseline and recoverable backups

- Run `python backend/manage.py release_check` (with a configured `.env`) for the release configuration gate. For production use a unique `DJANGO_SECRET_KEY`, HTTPS, restricted hosts, and a production application server. `DEBUG=true` is **local-only**.
- Run `python scripts/backup_restore.py backup --archive backups/docupilot_snapshot.backup.zip` and `verify --archive ...` for SQLite3 snapshot and private media checksums. Restore is intentionally dry-run unless explicitly confirmed; it refuses to overwrite any existing data.
- Execute `python -m unittest discover -s scripts -p "test_*.py"`, Django tests, frontend tests, Playwright and the React build as documented in [PHASE5_STEP1_TESTING.md](PHASE5_STEP1_TESTING.md).
- Preserve [LICENSE](LICENSE), [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md). This update does not add PostgreSQL or change database migrations.
- **Do not call this a public-production-ready deployment:** HTTP Basic authentication and rate limiting need a dedicated security remediation step. Independent classification evaluation is still contingent on genuine adjudicated labels.
