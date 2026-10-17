# Phase 1 Step 3 — Windows 11 verification

From the repository root in VS Code PowerShell:

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
python manage.py runserver
```

Expect clean system checks, no outstanding migrations, successful test suite, and server listening at `http://127.0.0.1:8000/`.

Use your existing Basic Authentication superuser (`admin` below is a placeholder), upload a PDF or TXT invoice and run document text extraction first:

```powershell
curl.exe -u admin -F "file=@invoice.txt" -F "title=Example Invoice" http://127.0.0.1:8000/api/documents/upload/
curl.exe -u admin -X POST http://127.0.0.1:8000/api/documents/1/extract/
curl.exe -u admin -X POST http://127.0.0.1:8000/api/documents/1/invoice/extract/
curl.exe -u admin http://127.0.0.1:8000/api/documents/1/records/
curl.exe -u admin http://127.0.0.1:8000/api/invoices/
```

Replace document ID `1` with the actual uploaded ID. Expected: 201 for valid invoice record creation, `unreviewed` validation status, page-number evidence for every recognized field, and null for unknown fields. A 422 response is expected if there is no extracted text or recognized invoice identifier. Verify another user cannot access the document or its records.

In a second PowerShell terminal, from the repo root:

```powershell
cd frontend
npm install
npm run build
npm run dev
```

Existing frontend should remain functional. No new invoice frontend page is claimed in this phase. No migration is needed for Step 3 because `ExtractedRecord` already has a JSON field.
