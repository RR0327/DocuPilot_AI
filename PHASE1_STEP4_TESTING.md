# Phase 1 Step 4 — Windows 11 verification

From repository root in **PowerShell**:

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

Expected: `core.0003_documentchunk` applied, no outstanding migrations, all tests pass. The exact test count may differ from prior releases. Create an authenticated user with `python manage.py createsuperuser` if needed. For manual REST checks use the Django Basic authentication-supported curl commands below (replace `admin` and document IDs):

```powershell
@'
Refund policy: Refund requests are accepted within thirty days of purchase.
'@ | Set-Content -Encoding utf8 policy.txt
curl.exe -u admin -F "file=@policy.txt" -F "title=Refund Policy" http://127.0.0.1:8000/api/documents/upload/
curl.exe -u admin -X POST http://127.0.0.1:8000/api/documents/1/extract/
curl.exe -u admin -H "Content-Type: application/json" -d '{"question":"What is the refund policy?","document_ids":[1]}' http://127.0.0.1:8000/api/ask/
```

PowerShell native quoting for JSON can vary. If `curl.exe -d` behaves unexpectedly, write a UTF-8 JSON file and send `--data-binary "@question.json"` instead. Expected Q&A response: HTTP 200, `has_evidence: true`, exact source excerpt, title, page number, and persisted question ID. Query unrelated text to verify `has_evidence: false` and explicit insufficient-evidence response. Try an unauthorized document ID to confirm HTTP 404.

Reprocess the same document and confirm chunks are not duplicated. Run prior Step 1–3 regression tests and verify invoice extraction still works. Frontend smoke test from the root:

```powershell
cd frontend
npm install
npm run build
npm run dev
```

Expected: frontend builds and opens at http://localhost:5173. This step delivers a backend Q&A API, **not yet a frontend chat UI**. The search is lexical, not semantic; non-matching synonyms may produce no results. Scores are relevance rankings, not confidence percentages.
