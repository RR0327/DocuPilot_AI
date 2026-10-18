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
