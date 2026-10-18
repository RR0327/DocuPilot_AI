# Phase 4 Step 6 — Reliability / independent adjudication acceptance

## Security and release status
- SQLite3, Tech_Innovators, private storage, existing REST endpoints and licensing unchanged.
- Classification operational review agreement is **not** independent accuracy.
- The evaluation input is local, user-supplied and needs two blind review labels and a final adjudicated label. Template data is **not** an independent dataset.
- Provenance fields are syntactically required, but declarations of reviewer independence/license **cannot be authenticated by code**. Manually audit source consent and protocol.
- Default evaluation report omits case details; do not publish the labeled source document dataset.
- No new migrations. No external AI model or service is needed.

## Windows PowerShell — from repository root
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
cd backend
python manage.py check
python manage.py migrate
python manage.py makemigrations --check --dry-run
python manage.py test core.test_adjudication core.test_reliability --verbosity 2
python manage.py test --verbosity 2
```

## Genuine independent evaluation
1. Ensure consent/license to use every document and create labels without exposing document text in a public report.
2. Obtain separate blind labels from two reviewers (`reviewer_a`, `reviewer_b`). Resolve disagreement with an adjudicator, documenting reasons.
3. Populate `backend/evaluation/adjudicated_labels_TEMPLATE.json` with actual cases and provenance; save as a new private file, e.g. `evaluation/adjudicated_private.json`.
4. Within backend run:
```powershell
python manage.py evaluate_adjudicated_classification --dataset evaluation/adjudicated_private.json --output adjudicated_report.json
```
5. Confirm report metrics, per-category supports, unsafe guesses, false abstentions, evidence issues and disagreement count. Keep the original dataset private.
6. Confirm the default report omits individual source pages, text and case identifiers.

## Frontend — from repository root
```powershell
cd frontend
npm install
npm test
npx playwright install chromium
npm run test:e2e
npm run build
npm run dev
```

Verify the new **Reliability** page after login; logout; ensure anonymous requests reject access and owner A never sees owner B's statistics. Confirm all pre-existing processing, OCR, invoice, analytics, PDF evidence, classification, and review workflows still work. Run actual Celery/Redis scenarios only if optional async mode is enabled.

## Release gate
- All backend tests, frontend tests, React build and security checks pass.
- Independent evaluation has non-synthetic representative examples and verified consent/provenance.
- Investigate class imbalance, unsafe guesses, OCR errors and evidence-grounding failures; document unresolved risks.
- **Local demo acceptance is not production security approval**. SQLite/Celery solo on Windows is not production HA infrastructure.
