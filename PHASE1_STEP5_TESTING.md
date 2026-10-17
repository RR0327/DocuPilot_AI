# Phase 1 Step 5 — Windows 11 verification

Keep your existing SQLite `backend/db.sqlite3` when updating. Never overwrite `.env` with example values.

From the repository root (PowerShell):

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

Expected: `core.0004_invoicepaymentstate` applied, no new migrations required, all tests green.

Authenticate with the same Basic authentication used for the existing protected endpoints (local testing only):

```powershell
curl.exe -u admin http://127.0.0.1:8000/api/invoices/dashboard/
curl.exe -u admin http://127.0.0.1:8000/api/invoices/report/
curl.exe -u admin -OJ http://127.0.0.1:8000/api/invoices/export/
curl.exe -u admin -X PATCH -H "Content-Type: application/json" -d '{"payment_status":"pending"}' http://127.0.0.1:8000/api/invoices/1/payment-status/
```

PowerShell can alter literal JSON quoting passed to curl.exe; if the final command fails, instead create `state.json` with `'{"payment_status":"pending"}' | Set-Content -Encoding ascii state.json` and run `curl.exe -u admin -X PATCH -H "Content-Type: application/json" --data-binary "@state.json" http://127.0.0.1:8000/api/invoices/1/payment-status/`. Replace `admin` and invoice record ID with real values.

`pending` and `paid` are **user-asserted states**, never inferred from invoices. Overdue pending counts exclude unknown and paid invoices. Currency totals are reported separately and missing/invalid amounts are excluded. Financial records remain `unreviewed` unless separately validated.

From another terminal in repository root:

```powershell
cd frontend
npm install
npm run build
npm run dev
```

Expected: existing frontend builds and starts on localhost:5173.

API contract:
- `GET /api/invoices/dashboard/`: count and currency-separated pending totals.
- `GET /api/invoices/report/?payment_status=pending&due=overdue`: filtered report; optional `document_id`, `due_from`, `due_to`.
- `GET /api/invoices/export/`: UTF-8 BOM CSV, same filters and owner scoping.
- `PATCH /api/invoices/{record_id}/payment-status/`: JSON `{"payment_status":"pending"}`; choices `unknown`, `pending`, `paid`, `disputed`.

Original `GET /api/invoices/` is unchanged for backward compatibility.
