# Phase 2 Step 1 — OCR acceptance (Windows 11)

## Prerequisites
- Install Tesseract OCR for Windows and ensure `tesseract --version` works in a **new** terminal.
- To configure a non-PATH install set `DOCUPILOT_TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe` in `.env`.
- English OCR uses `DOCUPILOT_OCR_LANG=eng`. Optional Bangla requires installed `ben.traineddata` and `DOCUPILOT_OCR_LANG=eng+ben`.
- This module is local/offline OCR, no paid API.

## Backend tests — project root PowerShell
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
tesseract --version
cd backend
python manage.py check
python manage.py migrate
python manage.py makemigrations --check --dry-run
python manage.py test --verbosity 2
python manage.py runserver
```
The `tesseract --version` command is optional if you've set `DOCUPILOT_TESSERACT_CMD`; verify the configured executable manually instead.
Expected: all checks and tests pass; no new migration. OCR packages installed. Backend at 127.0.0.1:8000.

## Frontend — separate terminal from root
```powershell
cd frontend
npm install
npm test
npx playwright install chromium
npm run test:e2e
npm run build
npm run dev
```
Expected: all frontend tests, browser tests, build pass; Vite on localhost:5173.

## Manual live workflow
1. Sign in using a Django test account.
2. Upload a scanned PDF with visible words, a PNG, and a JPEG (max 10 MiB each).
3. Press Extract text and inspect page-level OCR evidence.
4. Verify indexed OCR text is searchable via Ask Documents with the correct page reference.
5. Upload a text-based PDF and TXT and ensure their extraction still works.
6. Upload a malformed PNG/JPEG and ensure a validation error, not HTTP 500.
7. Create a second Django account and confirm it cannot retrieve another owner's OCR text or files.
8. Re-extract a scanned PDF and confirm no duplicate `DocumentPage` or `DocumentChunk` rows.
9. Temporarily configure an invalid Tesseract executable, then verify extraction gives HTTP 422 and status failed rather than exposing server paths.

## Limits and caveats
- Supported: text PDF, scanned PDF, UTF-8 TXT, PNG, JPEG.
- OCR runs only for PDF pages without extractable text (mixed-mode documents supported).
- Each upload <= 10 MiB; OCR on up to 50 textless PDF pages per file, pixel limit 20 million per image/page, 25-second OCR subprocess timeout per page.
- Blank scans can return 422 with no readable text. OCR accuracy is not guaranteed and requires manual verification.
- Do not upload sensitive files to an externally accessible development server. Configure HTTPS and stronger authentication before production.
