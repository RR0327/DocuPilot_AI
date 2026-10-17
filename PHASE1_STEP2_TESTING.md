# Phase 1 Step 2 — Windows 11 testing

Run PowerShell in the extracted `DocuPilot_AI` repository root.

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

Expected: clean Django check, no new migration changes, tests pass, server on http://127.0.0.1:8000/. Keep the backend terminal running. Open another PowerShell terminal at repository root:

```powershell
cd frontend
npm install
npm run build
npm run dev
```

Expected: frontend build passes, Vite runs at http://localhost:5173/.

## Manual API verification

Create a superuser from the `backend` directory (`python manage.py createsuperuser`), then create a UTF-8 test file:

```powershell
Set-Content -Path sample.txt -Value 'Invoice 42 - BDT 500' -Encoding utf8
curl.exe -u admin -F 'file=@sample.txt' -F 'title=Invoice sample' http://127.0.0.1:8000/api/documents/upload/
```

Replace `admin` with your username. Record the returned document `id`, then replace `<ID>` in the following commands:

```powershell
curl.exe -u admin -X POST 'http://127.0.0.1:8000/api/documents/<ID>/extract/'
curl.exe -u admin 'http://127.0.0.1:8000/api/documents/<ID>/pages/'
curl.exe -u admin 'http://127.0.0.1:8000/api/documents/<ID>/'
```

Expected: extraction HTTP 200 with `processing_status=completed`, `page_count=1`; pages response contains page 1 with `Invoice 42 - BDT 500`; details contain completed status. Re-run extraction and confirm no duplicate page.

A text-based multi-page PDF should produce one `DocumentPage` per PDF page. A header-only fake PDF may upload but extraction must return HTTP 422 and status `failed`. A scanned PDF without text also returns 422; OCR is reserved for Phase 2. Users must not be able to retrieve or extract another user's document.

**Limitations:** extraction is synchronous, files are capped at 10 MiB, PDFs at 500 pages, and TXT files are represented as one logical page. This phase does not perform OCR, search or invoice field extraction. Avoid running large files on a development server intended for many concurrent users.
