# Phase 3 Step 1 — Human Review Queue: Windows 11 verification

## Upgrade precautions
Preserve your real `.env`, `backend/db.sqlite3` and `backend/private_media` before updating. Never overwrite your SQLite database with a fresh archive. Keep Tesseract and optional semantic dependencies from earlier phases.

## Backend
From the repository root, in Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
cd backend
python manage.py check
python manage.py migrate
python manage.py makemigrations --check --dry-run
python manage.py test core.test_review --verbosity 2
python manage.py test --verbosity 2
python manage.py runserver
```

Expect migration `core.0007_extractionreview` to apply; six review tests and all prior regression tests should pass. No paid API or PostgreSQL is required.

## Frontend
In a second terminal, from the repository root:

```powershell
cd frontend
npm install
npm test
npx playwright install chromium
npm run test:e2e
npm run build
npm run dev
```

Expect 14 existing unit tests, successful browser tests/build and app at http://localhost:5173.

## Manual API tests
Create a Django account with `python manage.py createsuperuser` if needed. Upload and extract an invoice as done in Phase 2; use the extracted **record ID** (not document ID) below.

```powershell
curl.exe -u admin http://127.0.0.1:8000/api/reviews/
curl.exe -u admin http://127.0.0.1:8000/api/reviews/1/
'{"action":"approve","corrections":{"total":"250.00"},"note":"Checked page 1"}' | Set-Content -Encoding ascii review.json
curl.exe -u admin -X POST -H "Content-Type: application/json" --data-binary "@review.json" http://127.0.0.1:8000/api/reviews/1/
curl.exe -u admin http://127.0.0.1:8000/api/invoices/report/
'{"action":"reopen","note":"Recheck"}' | Set-Content -Encoding ascii reopen.json
curl.exe -u admin -X POST -H "Content-Type: application/json" --data-binary "@reopen.json" http://127.0.0.1:8000/api/reviews/1/
```

Replace `admin` and `1` appropriately. Approve should return `valid`, original/effective field distinctions and an audit event; report should reflect a corrected approved value. Reopen should return `unreviewed`, retain historical events and restore original report value until approval. Reject requires a nonempty note. Unauthorized or cross-user accesses must be denied. Review statuses are *unreviewed*, *valid* and *invalid*, preserving legacy contracts.

## Operational limitations
- Owner-only review: there is no separate organization-wide reviewer role in this phase.
- Flags are deterministic diagnostics, not calibrated ML confidence probabilities.
- Corrections are field-level overlays in audit events; original extraction, page evidence and line items are not rewritten.
- A newly extracted invoice creates a new unreviewed record. Previous approvals remain on their prior record.
- Revalidating corrected totals against original OCR line items requires human review; approval is a human attestation, not algorithmic proof.
- These are local development credentials; HTTP Basic requires HTTPS for remote deployment.
