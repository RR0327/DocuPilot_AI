# DocuPilot AI — Phase 4 Step 1: Explainable Document Classification

Copyright (c) 2026 Tech_Innovators. MIT License.

## Scope

- Document categories: `invoice`, `policy`, `report`, `contract`, `unknown` (abstention).
- Deterministic, transparent rule-based classification from stored `DocumentPage.extracted_text`, including prior OCR output. **Not a trained machine-learning classifier.**
- Each decision records bounded phrase matches, page numbers, excerpts, weighted rule scores and a reason. **Weighted scores are not calibrated confidence percentages.**
- One latest classification per document, automatically refreshed after successful sync or Celery extraction, and manually refreshed using the owner-only POST route.
- Original source files/pages remain unchanged. `DocumentClassification` persists in SQLite3 and is deleted with its document.
- Classification may be wrong on unfamiliar templates or multilingual content. Do not use without manual review in consequential workflows.

## Install: Windows 11 PowerShell (project root)

Back up `.env`, `backend/db.sqlite3`, and `backend/private_media` before upgrading. Retain your existing database and uploads.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
python -m pip install -r backend/requirements-async.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
cd backend
python manage.py check
python manage.py migrate
python manage.py makemigrations --check --dry-run
python manage.py test core.test_classification --verbosity 2
python manage.py test --verbosity 2
python manage.py runserver
```

Expected: migration `core.0010_documentclassification` applies, no pending migrations, classification tests and full suite pass. If Django is unavailable, install packages as above. Optional Celery/Redis requirements support background processing; synchronous extract remains usable without a broker.

Frontend, in another PowerShell terminal from project root:

```powershell
cd frontend
npm install
npm test
npx playwright install chromium
npm run test:e2e
npm run build
npm run dev
```

Expected: **23 Node unit tests** pass, browser tests and Vite production build pass, frontend available at `http://localhost:5173`.

## API

- `GET /api/documents/{id}/classification/`: returns latest classification, or `404` if not yet classified.
- `POST /api/documents/{id}/classification/`: recalculates from stored pages, returns `409` if no pages exist or extraction is actively queued/running.
- `GET /api/documents/`: each item has `classification_category` (null until classified).
- Cross-user document IDs return `404` and unauthenticated requests return `401` or `403`.

Response fields: `document_id`, `category`, `evidence` (page_number, category, phrase, excerpt, rule weight), `rule_scores`, `reason`, `classified_at`, `calibrated_confidence: null`.

## Manual acceptance

1. Upload a UTF-8 TXT invoice with `Invoice No: 43`, `Invoice Date: 2026-10-15` and `Subtotal: 150`; click **Extract text**, inspect `Invoice` label and **View evidence**.
2. Upload policy (`Privacy Policy`, `Policy Scope`), report (`Executive Summary`, `Methodology`, `Findings`) and contract (`This Agreement`, `Governing Law`) fixtures; extract, verify each category, source page, and phrase excerpt.
3. Upload unrelated text; verify `Needs review` / `unknown`, not forced classification.
4. Run **Reclassify** and verify the current stored page content determines the result; it must not rewrite original pages.
5. Verify a different account cannot GET/POST classification for another user's document.
6. Verify async extraction invokes classification, and a queued job blocks reclassification.
7. Regression: PDF OCR, private PDF viewer, Q&A semantic/hybrid retrieval, invoice intelligence, human review, supplier analytics, async worker recovery.
8. Preserve `LICENSE`, `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, Tech_Innovators ownership, SQLite3 database and private file storage.

## Local validation caveat

Python syntax and frontend unit tests can be executed offline in the build environment. Django tests, migration execution, Playwright, live Celery/Redis and React production build must be verified in Windows if their dependencies are unavailable locally.
