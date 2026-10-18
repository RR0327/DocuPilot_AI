# Phase 3 Step 2 — Supplier Analytics: Windows 11 Verification

## Scope
Adds authenticated `GET /api/invoices/analytics/`, SQLite-compatible invoice-value aggregations, currency-separated monthly trends and supplier rankings, and a React Recharts view. No migrations needed. Original extraction and approved human-review corrections remain preserved. Financial metrics represent invoice *value*, **not actual cash spending**.

## Preserve local data
Back up `.env`, `backend/db.sqlite3` and `backend/private_media` before updating. Do not overwrite existing populated SQLite3 data.

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
python manage.py test core.test_supplier_analytics --verbosity 2
python manage.py test --verbosity 2
python manage.py runserver
```
Expected: `System check identified no issues`, no outstanding migrations, 5 new supplier analytics tests passing, all existing regression tests passing. The backend runs at `http://127.0.0.1:8000`.

## Frontend commands (second PowerShell, repository root)
```powershell
cd frontend
npm install
npm test
npx playwright install chromium
npm run test:e2e
npm run build
npm run dev
```
Expected: 18 frontend tests passing, Playwright suite passing, Vite build successful, UI served at `http://localhost:5173`. Recharts is a new dependency and requires `npm install`.

## API validation
Log in with an existing Django user in the React app, or call with curl Basic authentication **on localhost only**:
```powershell
curl.exe -u admin http://127.0.0.1:8000/api/invoices/analytics/
curl.exe -u admin "http://127.0.0.1:8000/api/invoices/analytics/?currency=BDT&year=2026&limit=5"
```
Replace `admin` with your own test username. Inspect `totals_by_currency`, `monthly_trends`, `top_suppliers`, `excluded_invoice_counts`, `basis`, and `date_basis` in the JSON.

## Manual acceptance dataset
Using your existing upload → extract text → extract invoice workflow, create three test invoice TXT files, each with explicit supplier, date, total, and currency. Example content for one:
```text
Supplier: Ceramic Hub
Invoice No: ANALYTICS-101
Invoice Date: 2026-08-12
Total Amount: BDT 125.00
```
Prepare a second invoice for `Ceramic Hub` dated 2026-09-01 totaling BDT 75.00 and a third for another supplier dated 2026-08-15 totaling USD 20.00. Confirm extraction values before relying on analytics. Open `Supplier analytics`; select BDT and then USD; verify the month grouping and that the amounts never combine across currencies.

Approve a corrected supplier or total in `Human review`; refresh analytics and confirm the approved effective value appears. Reopen the review to confirm analytics falls back to the original extracted values. Reject a sample invoice and verify exclusion. Test a second user to ensure they cannot see the first user's analytics. Confirm malformed filters return HTTP 400 and unauthenticated requests return HTTP 401/403.

## Accuracy and release limits
- An invoice without a valid explicit `invoice_date`, supplier, supported currency or usable total is excluded and counted by reason.
- Rejected invoices are excluded. Unreviewed invoices are **included**, so this is not an audited-spend ledger.
- Totals by currency are strictly separated, without currency conversion.
- `payment_status` is not used as a cash spending ledger; analytics values represent invoices issued, dated by invoice date.
- SQLite is appropriate for a local demo; benchmark before heavy multi-user deployment.
- The original REST endpoints, OCR, PDF viewer, Q&A, and review workflow must pass regression tests before moving ahead.
