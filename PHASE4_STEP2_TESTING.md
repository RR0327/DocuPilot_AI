# Phase 4 Step 2 — Classification Quality Evaluation and Acceptance

**Copyright © 2026 Tech_Innovators** · SQLite3 remains the only database.

## Scope

- The deterministic classifier continues to support **invoice, policy, report, contract, and unknown**; all existing OCR, Celery/Redis, private document delivery, Q&A, human review and supplier analytics workflows remain in place.
- `backend/evaluation/classification_cases.json` supplies **15 synthetic labeled cases**: three per category including abstentions (`unknown`). These do not measure production accuracy.
- `backend/core/classification_evaluation.py` computes multiclass precision, recall, F1, macro averages, accuracy, confusion matrix, and page-grounded evidence integrity diagnostics. Scores use `0.0` when a metric denominator is zero.
- Explainability cap refinement: evidence for the winning category appears first before the existing 12-excerpt cap is applied. The classification decision rules and weights are unchanged.
- `GET /api/classification/evaluation/` is authenticated and serves this bundled synthetic evaluation only; it never processes users' stored documents. `Classification quality` in React shows the report and confusion matrix.
- `python manage.py evaluate_classification --output classification_report.json` reproduces the same benchmark locally.

## Windows 11 instructions

**Back up** `.env`, `backend/db.sqlite3` and `backend/private_media` before upgrading. Preserve the existing database, rather than overwriting it with a blank copy.

From repository root, in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
cd backend
python manage.py check
python manage.py migrate
python manage.py makemigrations --check --dry-run
python manage.py test core.test_classification_evaluation core.test_classification --verbosity 2
python manage.py test --verbosity 2
python manage.py evaluate_classification --output classification_report.json
python manage.py runserver
```

Expected: no outstanding migrations, passing focused and full Django tests, and a `classification_report.json` containing 15 cases, all five labels, an evidence integrity count, per-class metrics and a confusion matrix. The included synthetic fixture is currently expected to yield perfect classification, **not a statement of real-world model quality**.

Open another PowerShell terminal **from the repository root**:

```powershell
cd frontend
npm install
npm test
npx playwright install chromium
npm run test:e2e
npm run build
npm run dev
```

Expected: 25 frontend Node unit tests pass and, in your environment, browser tests and the Vite build pass. Log into `http://localhost:5173`, select **Classification quality**. Confirm the synthetic label and that rows/columns in the confusion matrix follow the documented actual/predicted ordering.

## Owner isolation and API

```powershell
# curl.exe uses your existing Django username and password.
curl.exe -u USERNAME:PASSWORD http://127.0.0.1:8000/api/classification/evaluation/
```

An anonymous request must return HTTP 401 or 403. This endpoint is a static **synthetic benchmark**; it does not read or disclose other users' documents. The existing `/api/documents/{id}/classification/` endpoint still requires document ownership for individual-document evidence.

## Manual classification and explainability regression

1. Upload a text invoice with `Invoice No`, `Invoice Date` and `Subtotal`. Extract it and inspect classification evidence, original page numbers, and excerpts.
2. Upload policy (`Privacy Policy`, `Policy Scope`), report (`Executive Summary`, `Methodology`, `Findings`), and contract (`This Agreement`, `Governing Law`, `Termination Clause`) samples; confirm categories.
3. Upload a benign note without category signals; expect `unknown`. Upload tied invoice/policy signals; expect `unknown` rather than forced assignment.
4. Verify that displayed evidence is found on the cited stored page. Ensure the winning category's evidence is not hidden when a long document produces more than 12 matches.
5. Log in as a different user and confirm existing document-specific classification GET/POST endpoints do not reveal the first user's document.
6. Repeat extraction with Celery/Redis enabled as applicable, and confirm human review, invoice analytics, PDF evidence and keyword/semantic/hybrid retrieval remain functional.

## Interpretation and release limitations

- All 15 provided evaluation cases are **hand-authored synthetic regression examples**; accuracy, macro-F1 and unknown-class performance on this small set cannot establish external validity.
- Collect a larger, independently labeled and deduplicated real-world test corpus covering scanned and multilingual content. Track support and per-class errors rather than only macro averages.
- The existing rule weights are not calibrated probabilities. Do **not** call them confidence percentages.
- An evidence match validates text grounding, not the truth of the underlying OCR transcription. Real OCR accuracy requires trusted transcriptions and a separate evaluation.
- A successful classification benchmark does not certify public production readiness; authentication, HTTPS, document privacy, security, dependency updates, monitoring and operational backups need separate review.
