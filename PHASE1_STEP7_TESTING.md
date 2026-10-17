# Phase 1 Step 7 — MVP hardening and Windows 11 verification

## Preserve existing data
Copy `backend/db.sqlite3`, `backend/private_media/`, and `.env` to a secure backup before switching repositories. Never commit these files.

## Backend (PowerShell from repository root)
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test --verbosity 2
python manage.py runserver
```
Expected: no check errors or pending migrations, all tests pass, API available on port 8000.

## Frontend (new PowerShell terminal from repository root)
```powershell
cd frontend
npm install
npm test
npx playwright install chromium
npm run test:e2e
npm run build
npm run dev
```
Expected: Node API tests and four mocked-browser workflows pass; `dist/` is generated.

**Important:** The browser suite mocks `/api` requests, so it validates real React UI behavior and frontend/API contracts, not live Django integration. Separately perform this live smoke test against Django: sign in; upload a small PDF and UTF-8 TXT; extract and view page text; extract an invoice; mark it pending; review dashboard/CSV; ask a question and examine its evidence; delete a test document; sign out; log in as a second user and verify owner isolation. Avoid using real sensitive documents.

## Release blockers and limitations
- HTTP Basic credentials are held in memory only. Production requires HTTPS, stronger authentication/session controls, rate limiting, and CSRF/CORS review.
- SQLite is suitable for local MVP; not validated for concurrent production workloads.
- Text-based PDFs only; OCR and semantic retrieval are later-phase features.
- Evidence extraction is keyword-based; outputs are not automatically verified.
- Browser E2E uses deterministic mocked data; it is **not** proof of a successful live backend E2E run.
- No claim of production readiness until live tests, security review and backup restore drill pass.

## Suggested release gate
Require: Django suite green, JS unit suite green, Playwright green, Vite build green, live end-to-end smoke green, ownership isolation confirmed, restore drill complete, and zero unresolved critical vulnerabilities. If any gate fails, mark release **NO-GO**.
