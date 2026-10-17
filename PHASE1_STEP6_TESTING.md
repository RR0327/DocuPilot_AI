# Phase 1 Step 6 — Windows 11 Verification

## 1. Preserve existing user data

Do not replace an existing `backend/db.sqlite3`, `backend/private_media/`, or `.env` with a clean ZIP copy. Back them up first. Keep the SQLite database and private file storage together.

## 2. Backend setup (PowerShell, repository root)

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
python manage.py createsuperuser # only if you have no existing account
python manage.py runserver
```

Expected: system check clean, SQLite migrations applied with no new changes, Django tests pass; server listens at `http://127.0.0.1:8000`.

## 3. Frontend setup (new PowerShell terminal, repository root)

```powershell
cd frontend
npm install
npm test
npm run build
npm run dev
```

Expected: six Node API regression tests pass, Vite build creates `frontend/dist/`, and site loads at `http://localhost:5173`.

## 4. Manual UI checks

1. **Authentication:** Log in with a valid Django user; expect sidebar and workspace. Wrong password must display an auth error. Sign out then reload; the user should be signed out (credentials are not persisted).
2. **Upload:** Select a small text-based PDF or UTF-8 TXT and upload. Expect confirmation and an entry under Your documents. Try an invalid extension; expect validation error. Documents above 10 MiB must be rejected.
3. **Extract:** Click Extract text; expect successful page/character counts. Click View pages; source text and page number should appear. Textless/scanned PDFs should require OCR.
4. **Invoice:** Upload an invoice such as a UTF-8 TXT with labeled Invoice No, Supplier, Invoice Date, Due Date, Subtotal, Tax, Total Amount. Extract text, then Extract invoice; see the extracted record on the Invoice intelligence tab. Unknown/missing fields must not be fabricated.
5. **Payment status:** New invoices must start `unknown`. Change status to `pending`, `paid`, or `disputed`; refresh and confirm it persists. Overdue counts apply only to explicitly pending and past-due invoices. Currency totals remain separate.
6. **Filtering and export:** Filter invoice report by payment status or due category, click Apply filters, then Export CSV; check file contents and that the export uses identical filters.
7. **Q&A:** Ask a specific question about indexed text, optionally select a document. Expect an extractive passage and document/page evidence. Ask about absent information; expect explicit insufficient evidence.
8. **Security:** Create a second regular user. Sign in as that user and confirm the first user's documents, invoices and Q&A sources do not appear. The backend automated tests also enforce ownership.
9. **UX:** Verify empty, loading and error states, keyboard focus and mobile layout. Disconnect the backend; the UI must show a connection error.
10. **Regression:** Re-run Django tests and `npm test`, `npm run build`; confirm prior endpoint behavior and exact root documentation filenames `README.md`, `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`.

## 5. Known MVP limitations

- Existing Django Basic authentication is used for speed. Credentials are in React state, not persisted. Local Vite requests may use HTTP; never send credentials across an untrusted network. Use TLS and reviewed authentication before remote use.
- Django paginates the document list; this frontend currently displays the first 20 documents only.
- No scanned-document OCR, LLM summarization, highlighted PDF viewer, or automated payment verification yet.
- Frontend automated tests cover HTTP integration helpers; comprehensive browser end-to-end tests are future work. Manual UI verification is mandatory.

## 6. Troubleshooting

- `403/401`: verify username/password and that the Django account is active.
- `Cannot connect to backend`: start `python manage.py runserver` on port 8000.
- `No module named django`: activate `.venv` and reinstall `backend/requirements.txt`.
- `npm is not recognized`: install Node.js LTS and reopen PowerShell.
- `Failed to fetch`: check Vite proxy and the backend process.
- React build failure: copy the full `npm run build` output; do not mark the build test passed.
