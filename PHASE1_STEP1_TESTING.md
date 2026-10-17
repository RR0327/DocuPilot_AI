# Phase 1 Step 1 — Windows 11 verification

From repository root in PowerShell:

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
python manage.py createsuperuser
python manage.py runserver
```

Use a second PowerShell terminal, in `backend/`, and create an example PDF:

```powershell
[System.IO.File]::WriteAllBytes((Join-Path (Get-Location) 'sample.pdf'),[System.Text.Encoding]::ASCII.GetBytes("%PDF-1.4`nexample"))
curl.exe -u admin:YOUR_PASSWORD -F "file=@sample.pdf;type=application/pdf" -F "title=Smoke test" http://127.0.0.1:8000/api/documents/upload/
curl.exe -u admin:YOUR_PASSWORD http://127.0.0.1:8000/api/documents/
```

Replace `admin` with your Django superuser username, and `YOUR_PASSWORD` with your actual password. Prefer `curl.exe -u admin` (which prompts for the password) on shared machines to avoid storing passwords in shell history. Expect 201 for upload and 200 for listing. For deletion, use the returned document ID:

```powershell
curl.exe -u admin -X DELETE http://127.0.0.1:8000/api/documents/1/
```

Expect 204 for an owned document, 404 for another user's document, and 401/403 when unauthenticated. The smoke-test PDF checks upload validation only; it is not a real parseable invoice.

Frontend regression from root:

```powershell
cd frontend
npm install
npm run build
npm run dev
```

Expected: existing frontend loads on http://localhost:5173 and API health works at http://127.0.0.1:8000/api/health/.
