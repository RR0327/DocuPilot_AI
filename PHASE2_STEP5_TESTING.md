# Phase 2 Step 5 — Windows 11 Evaluation and Release Gate

## Upgrade safely

Back up `.env`, `backend/db.sqlite3`, and `backend/private_media` before updating source code. Never commit these. Preserve the `LICENSE`, `CONTRIBUTING.md`, `README.md`, and `SECURITY.md` filenames. SQLite3 remains the only required database. This update requires **no migration**.

## Backend commands (PowerShell, repository root)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
cd backend
python manage.py check
python manage.py migrate
python manage.py makemigrations --check --dry-run
python manage.py test core.test_quality core.test_evaluation_metrics --verbosity 2
python manage.py test --verbosity 2
python manage.py evaluate_docupilot --mode keyword --output evaluation_keyword.json
python manage.py runserver
```

Expected: Django system check passes, no pending migrations, automated suites pass. The evaluation command prints JSON with retrieval Recall@5, MRR, no-evidence abstention rate, literal citation integrity, invoice field exact-match rate, and illustrative OCR CER. For the bundled synthetic fixture, expected keyword Recall@5 = 1.0, abstention = 1.0, citation integrity = 1.0, and invoice field exact-match = 1.0. Inspect the JSON rather than assuming universal model accuracy.

To evaluate **actual semantic/hybrid retrieval** using the locally installed model, first install `backend/requirements-semantic.txt`, allow model download and run:

```powershell
python manage.py evaluate_docupilot --mode semantic --output evaluation_semantic.json
python manage.py evaluate_docupilot --mode hybrid --output evaluation_hybrid.json
```

Different model results are possible. Do not label a synthetic fixture result as real-world accuracy. The command creates **temporary database fixtures and rolls back all inserts**. Do not run it simultaneously with a SQLite database backup or long-running write job.

## OCR evaluation

The sample OCR character-error rates are **illustrative comparisons**, not the output of live Tesseract inference. For real OCR acceptance, create a reviewed reference transcription of representative English and Bangla documents, compare actual OCR output against the reference, and calculate `character_error_rate(reference, predicted)` from `core.evaluation_metrics`. Include scanned PDFs, low-contrast images, and mixed-layout documents. Review factual fields and source pages manually. Run OCR while Tesseract is installed and inspect the errors; OCR quality depends on input.

## Invoice quality acceptance

Use at least two real or synthetic invoices: a clean table and a mismatched row. Check amount extraction, source excerpts, math warnings, new due-before-invoice warning, and recognized line-total versus subtotal warning. Those are **review flags, not auto-corrections**. Missing fields should remain null; paid/pending state must remain owner-entered. Verify owner and cross-user isolation.

## Frontend and browser regression (separate terminal)

```powershell
cd frontend
npm install
npm test
npx playwright install chromium
npm run test:e2e
npm run build
npm run dev
```

Expected: existing frontend unit/browser suites pass; Vite build succeeds; app loads at http://localhost:5173. Manually test PDF/TXT/image uploads, OCR, PDF evidence, keyword/semantic/hybrid Q&A, line items, payment overview and CSV export.

## Release assessment

Phase 2 can be approved for a **local demonstration** only after all runtime tests and a representative corpus review pass. Production use remains blocked by authentication hardening, OCR throughput limits, secure deployment, operational monitoring, backup recovery, and review of extraction accuracy on domain documents. No claim of production readiness is implied by passing synthetic fixtures.
