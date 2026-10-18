# Phase 4 Step 4 — Windows 11 acceptance and classification-feedback workflow

Copyright (c) 2026 Tech_Innovators. Preserve existing `.env`, `backend/db.sqlite3`, and `backend/private_media` before updating.

## Backend

From the project root in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
cd backend
python manage.py check
python manage.py migrate
python manage.py makemigrations --check --dry-run
python manage.py test core.test_classification_feedback --verbosity 2
python manage.py test --verbosity 2
python manage.py runserver
```

Expected: migration `core.0011_classificationfeedback` applies and the new and existing backend tests pass. No additional migration should be generated.

## Frontend

From project root in another PowerShell terminal:

```powershell
cd frontend
npm install
npm test
npx playwright install chromium
npm run test:e2e
npm run build
npm run dev
```

## Manual acceptance

1. Upload and extract an invoice and open *Review category / history*. Check predicted category, original evidence and page number.
2. Verify the prediction and observe a human label and history entry.
3. Enter a DIFFERENT category, reason, and Save override. Confirm the machine label has not changed.
4. Reclassify from stored pages: human feedback must remain independently recorded.
5. Clear review: the effective category returns to the current machine prediction, while previous history remains.
6. Check `GET /api/classification/feedback-evaluation/` returns owner-specific counts, not accuracy claims.
7. Login with a second user. Read, override and history access to the first owner's document must yield 404.
8. With an active queued/running extraction job, POST review must return 409.
9. Verify OCR, Celery/Redis, invoice review, supplier charts, PDF evidence, semantic/hybrid search and original classification evaluation still work.

## API

`GET /api/documents/{id}/classification-review/` retrieves current machine and human categories and append-only events.
`POST /api/documents/{id}/classification-review/` with JSON `{ "action": "verify" }`, `{ "action": "override", "category": "policy", "note": "Checked original document" }`, or `{ "action": "clear" }`.
`GET /api/classification/feedback-evaluation/` returns owner-scoped review counts, explicitly NOT independent classification accuracy.

## Known limitations

- Owner review is not an independent, blinded, two-annotator gold standard. Do not interpret review counts as precision/recall/F1.
- Machine evidence from last classification is retained separately from human decisions; old events record the machine category at decision time.
- SQLite concurrency is suitable for a local demonstration, not high-concurrency reviewer teams.
- Django and browser integration were not executable in the generation environment; run the commands above before release acceptance.
