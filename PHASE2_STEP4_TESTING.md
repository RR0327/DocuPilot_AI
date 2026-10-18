# DocuPilot AI — Phase 2 Step 4 verification (Windows 11)

Copyright © 2026 Tech_Innovators · MIT License

## Upgrade without losing data

Back up `.env`, `backend/db.sqlite3`, and `backend/private_media` from the **existing**
working repository. Extract the new full repository. Restore these private files if
using a fresh directory. Do not commit the database or private uploads to Git.

## Django and SQLite3

Start in the `DocuPilot_AI` root in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
cd backend
python manage.py check
python manage.py migrate
python manage.py makemigrations --check --dry-run
python manage.py test core.test_line_items --verbosity 2
python manage.py test --verbosity 2
python manage.py runserver
```

Expect the `0006_invoicelineitem` migration to apply (or be already applied), no
pending model changes, five line-item tests passing and the full Django suite passing.
Existing API and security tests must still pass.

## React

In a **second** PowerShell terminal from the repository root:

```powershell
cd frontend
npm install
npm test
npx playwright install chromium
npm run test:e2e
npm run build
npm run dev
```

Expect **14 frontend unit tests** to pass; all Playwright scenarios and Vite build
must pass on the developer's machine. Open http://localhost:5173.

## End-to-end invoice test

Create `backend/line_invoice.txt` containing:

```text
Supplier: Example Ltd
Invoice No: LINE-2026-001
Invoice Date: 2026-10-12
Description | Qty | Unit Price | Amount
Ceramic Tile | 2 | 125.50 | 251.00
Transport Fee | 1 | 20.00 | 21.00
Subtotal: BDT 272.00
Total Amount: BDT 272.00
```

In the React interface: sign in, upload that TXT file, extract text, extract invoice,
open **Invoice intelligence**, and click **Line items** for the new record. Expect
2 lines: Ceramic Tile is `matched`, Transport Fee is `mismatch`; source page 1 on
both lines. The discrepancy requires human review, not automatic correction.

Alternatively, with a local Django account (`admin` is a placeholder):

```powershell
curl.exe -u admin -F "file=@line_invoice.txt" -F "title=Line Invoice" http://127.0.0.1:8000/api/documents/upload/
# Replace DOCUMENT_ID and RECORD_ID below with actual API response IDs:
curl.exe -u admin -X POST http://127.0.0.1:8000/api/documents/DOCUMENT_ID/extract/
curl.exe -u admin -X POST http://127.0.0.1:8000/api/documents/DOCUMENT_ID/invoice/extract/
curl.exe -u admin http://127.0.0.1:8000/api/invoices/RECORD_ID/line-items/
```

Confirm the row response contains `quantity`, `unit_price`, `line_total`,
`calculated_total`, `validation_status`, `page_number`, `source_excerpt`.
Unauthenticated access must return 401/403; a second user must receive 404.

## Regression checks

- Old invoice fields, due-date dashboards, payment statuses and CSV export work.
- PDF private viewing, OCR, page-level evidence, keyword/semantic/hybrid Q&A work.
- No line item is inferred without a recognizable header and all numeric columns.
- Existing extracted records are not overwritten when invoice extraction runs again.
- Deleting a document cascades to its invoice records and line items.

## Status of verification in packaging environment

Python syntax checks, ZIP tests, and the 14 frontend unit tests were completed.
Django migrations/runtime tests, Playwright tests and React production build must
be run on Windows 11; do not represent them as already passed.
