# DocuPilot AI — Phase 2 Step 3 verification (Windows 11)

## Before updating
Back up `.env`, `backend/db.sqlite3`, `backend/private_media` and any other private document storage. Keep the four canonical filenames `README.md`, `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md` unchanged.

## Backend terminal (repository root, PowerShell)
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
# Optional semantic search:
# python -m pip install -r backend/requirements-semantic.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
cd backend
python manage.py check
python manage.py migrate
python manage.py makemigrations --check --dry-run
python manage.py test --verbosity 2
python manage.py test core.test_private_pdf --verbosity 2
python manage.py runserver
```
No database migration is added in this step. Expect `No changes detected`, all backend tests passing, and `http://127.0.0.1:8000/api/health/` returning status ok.

## Frontend terminal (repository root, PowerShell)
```powershell
cd frontend
npm install
npm test
npx playwright install chromium
npm run test:e2e
npm run build
npm run dev
```
Expected 13 frontend unit tests passing; browser tests and production build must be run on Windows because npm dependency installation timed out in the packaging environment.

## End-to-end manual evidence checks
1. Sign in with an ordinary Django user.
2. Upload a **text-layer PDF** containing a unique sentence; click Extract text, then Ask documents with a matching query.
3. Click **View highlighted PDF** beneath its source. Ensure the requested page renders and matching text-layer words are marked. Test previous/next/go-to-evidence buttons.
4. Upload a **scanned PDF** and extract with Tesseract. Ask a question; open source PDF and confirm source text appears in the separate excerpt, while no fake positional highlight is suggested when the PDF lacks a text layer.
5. Sign in as a second user. Request `GET /api/documents/<first-user-id>/private-pdf/` and verify HTTP 404; anonymous access should be 401/403.
6. Verify direct private storage file paths are not publicly served. Confirm private response uses `Cache-Control: private, no-store` and no filesystem path in `Content-Disposition`.
7. Re-extract, delete documents, and sign out; confirm no outdated evidence remains. Re-run previous invoice, OCR, search and regression tests.

## Known limits and security notes
- Word highlighting is approximate matching against PDF.js text items, not exact character bounding boxes. OCR-only pages intentionally display source text separately.
- Credentials for HTTP Basic must never traverse non-HTTPS public networks. The existing local MVP authentication is not production hardened.
- Browser PDFs and OCR may contain sensitive content; do not upload confidential data to public demonstrations.
- No live Django or production-build pass has been asserted in this environment.
