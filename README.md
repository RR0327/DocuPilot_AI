# DocuPilot AI

**Intelligent Document Processing & Knowledge Assistant**  
**Maintained by:** Tech_Innovators  
**Status:** Phase 0 Step 2 — SQLite and API foundation

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Contributing](https://img.shields.io/badge/Contributing-Guidelines-2ea44f)](CONTRIBUTING.md)
[![Security](https://img.shields.io/badge/Security-Policy-orange)](SECURITY.md)

[License](LICENSE) · [Contributing Guidelines](CONTRIBUTING.md) · [Security Policy](SECURITY.md)

> **Development notice:** This repository currently contains the Phase 0 Step 2 database and API foundation. Features described as planned below are not yet implemented. Do not upload confidential or regulated documents to this development build.

## Overview

DocuPilot AI is an open-source project to help organizations upload business documents, extract structured information, search relevant passages, and answer questions with traceable document and page references. The goal is evidence-grounded document intelligence rather than unsupported chatbot responses.

**Example use cases (planned):**
- Extract invoice number, supplier, dates, subtotal, tax, and total amount.
- Find invoices approaching or past their payment due date.
- Ask questions about policies, reports, and manuals with page-level citations.
- Review extracted information and export invoice records.

## Current capabilities

- Django REST Framework backend with a health endpoint at `/api/health/`.
- React + Vite + Tailwind CSS starter frontend, connected to the API through a Vite proxy.
- Backend smoke tests and React production-build command.
- Django default SQLite3 database, Django migrations, document metadata models, and owner-isolated authenticated API scaffolding.
- File upload and AI functions return HTTP 501 until their Phase 1 implementations are delivered.

**Not implemented yet:** document upload, parsing, invoice extraction, Q&A, authentication workflows, OCR, semantic retrieval, production deployment.

## Planned technology stack

| Layer | Technology |
| --- | --- |
| Frontend | React, Vite, Tailwind CSS |
| Backend/API | Python, Django, Django REST Framework |
| Database | SQLite3 (Django default; no separate installation) |
| Document extraction | PyMuPDF, Pydantic (planned) |
| Search | SQLite-backed metadata; keyword retrieval planned for MVP; hybrid/semantic search later |
| OCR | Tesseract or EasyOCR (Phase 2) |
| Async jobs | Celery and Redis (Phase 3) |
| Analytics | Recharts (Phase 3) |
| Deployment target | Vercel frontend, Render backend (subject to production review) |

## Roadmap

| Phase | Scope | Status |
| --- | --- | --- |
| 0 — Foundation | Starter frontend/backend, SQLite configuration, models, migration and API scaffolding | In progress |
| 1 — MVP | Document workspace, text-based PDF extraction, structured invoice records, evidence-linked Q&A, filtering and CSV export | Planned |
| 2 — Advanced processing | OCR, semantic/hybrid retrieval, highlighted evidence viewer, invoice line items | Planned |
| 3 — Operations | Human review queue, supplier analytics, background processing | Planned |
| 4 — Enterprise | Classification, multi-document Q&A, roles/permissions, audit logs | Planned |
| 5 — Production readiness | Hardening, deployment checks, documentation and release handoff | Planned extension |

## Getting started on Windows 11

### Prerequisites

- Python 3.12
- Node.js 22 LTS or newer and npm
- PowerShell / Windows Terminal
- Git (recommended)

### 1. Clone and configure

```powershell
git clone https://github.com/YOUR_GITHUB_USERNAME/docupilot-ai.git
cd docupilot-ai
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
Copy-Item .env.example .env
```

Replace `YOUR_GITHUB_USERNAME` with the account or organization that hosts this project. If working from a downloaded ZIP instead, open PowerShell in the extracted `DocuPilot_AI` directory and skip `git clone` and `cd docupilot-ai`.

The `.env` file is for local configuration and must **never** be committed. Change example credentials before any public deployment.

### 2. Run and test the backend

```powershell
cd backend
python manage.py check
python manage.py migrate
python manage.py test
python manage.py runserver
```

Expected: the system check completes without issues, the tests pass, and the server listens on `http://127.0.0.1:8000/`.

Health check: [http://127.0.0.1:8000/api/health/](http://127.0.0.1:8000/api/health/)

### 3. Run the frontend (a second PowerShell terminal)

From the repository root:

```powershell
cd frontend
npm install
npm run build
npm run dev
```

Visit [http://localhost:5173](http://localhost:5173). With the backend running, the starter UI should show **Backend connected**.

## Planned API endpoints

The following endpoints are from the project proposal and are **not all available in this starter build**:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/api/documents/upload/` | Upload documents |
| GET | `/api/documents/` | List documents |
| GET | `/api/documents/{id}/` | Document details |
| POST | `/api/documents/{id}/extract/` | Structured extraction |
| GET | `/api/documents/{id}/pages/` | Extracted pages and references |
| POST | `/api/ask/` | Evidence-grounded Q&A |
| GET | `/api/invoices/` | Invoice records |
| GET | `/api/invoices/export/` | CSV export |

## Responsible handling of information

This software is under active development. Planned safeguards include file validation, authorization, tenant/document isolation, auditability, evidence citations, and secure handling of uploaded files. **Some authorization scaffolding exists, but these safeguards are not complete.** Do not use this starter to process sensitive business data in production.

## Project documentation

- [License — MIT](LICENSE): terms for use, modification, and distribution.
- [Contributing Guidelines](CONTRIBUTING.md): development workflow and pull request expectations.
- [Security Policy](SECURITY.md): supported releases and vulnerability reporting guidance.

## Ownership and license

Copyright (c) 2026 **Tech_Innovators**.

Released under the [MIT License](LICENSE). Copyright ownership remains with Tech_Innovators for its original contributions; the MIT License permits reuse subject to its terms. Third-party dependencies retain their own licenses.

## Acknowledgments

Based on the **DocuPilot AI — Intelligent Document Processing & Knowledge Assistant** project proposal and roadmap.


## Phase 0 Step 2 — SQLite3 and document API foundation

SQLite3 is now the only configured database. It is included in Python and requires no PostgreSQL installation, server, credentials, or separate database creation. Running `python manage.py migrate` creates `backend/db.sqlite3` automatically. Do not commit this file to Git or deploy it as a multi-instance production database.

Run from the repository root in Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
Copy-Item .env.example .env  # Skip if .env already exists; remove old POSTGRES_ entries
cd backend
python manage.py check
python manage.py migrate
python manage.py makemigrations --check --dry-run
python manage.py test --verbosity 2
python manage.py runserver
```

The REST API foundation includes `GET /api/documents/`, `POST /api/documents/` (metadata only), `GET /api/documents/{id}/`, `GET /api/documents/{id}/pages/`, and `GET /api/documents/{id}/records/`. These endpoints require authentication; users may access only their own documents. `POST /api/documents/upload/`, `POST /api/documents/{id}/extract/`, and `POST /api/ask/` return `501 Not Implemented` for authenticated callers. This is intentional: no file handling or AI extraction is claimed in this step.

**Database trade-off:** SQLite is excellent for a time-constrained local prototype. PostgreSQL and pgvector remain optional future upgrades for high-concurrency production deployments or advanced vector search. Do not describe pgvector or PostgreSQL full-text search as implemented in this SQLite release.
