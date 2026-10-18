# Phase 4 Step 5 — Feedback quality and privacy-safe labels

## Windows 11
Back up `.env`, `backend/db.sqlite3` and `backend/private_media` first. Keep the populated SQLite database.

Backend from repository root (PowerShell):
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
cd backend
python manage.py check
python manage.py migrate
python manage.py makemigrations --check --dry-run
python manage.py test core.test_feedback_quality --verbosity 2
python manage.py test --verbosity 2
python manage.py runserver
```

Frontend from another terminal at repository root:
```powershell
cd frontend
npm install
npm test
npx playwright install chromium
npm run test:e2e
npm run build
npm run dev
```

## Manual acceptance
1. Upload and classify a document. Verify its machine label and make a different human override. Visit **Feedback quality** and check that the disagreement increases.
2. Verify a second document with the same machine label; check agreement increments. Clear one review and confirm it no longer counts in the current active comparison.
3. Reclassify a reviewed document and confirm the analysis compares the immutable machine label **at review time**, and records a changed-since-decision count.
4. Export the feedback snapshot after the confirmation prompt. Inspect its JSON; it must have random sample IDs and labels only, with no title, notes, source pages, document IDs, username or text.
5. Export again and ensure sample aliases change. Do **not** claim exported label pairs are independently adjudicated ground truth; a label-only dataset cannot calculate classifier recall/F1 over original documents.
6. Sign in with another owner and verify their aggregate report and export exclude all first-owner records. Anonymous access must be rejected.
7. Confirm unchanged OCR, semantic/hybrid search, invoice reports, PDF viewer, human invoice review, Celery job processing, and classification review workflows.

## Acceptance gate
- No new migration required; Django checks and full test suite pass.
- API coverage and agreement denominator exclude cleared and unreviewed cases.
- No PII or raw document contents in exports; no-store response headers present.
- Frontend unit tests, browser tests, and React production build pass.
- SQLite3, Tech_Innovators ownership, MIT LICENSE, CONTRIBUTING.md, README.md, and SECURITY.md remain in place.

### Known limitations
Owner feedback is subjective operational metadata and **not** independently verified ground truth. No new measured real-document accuracy is claimed; no training pipeline is added. Exported label-only metadata is privacy-minimizing but may still be sensitive in small or highly distinctive datasets, so users should inspect before sharing. SQLite3 is retained for local demonstration, not high-concurrency production.
