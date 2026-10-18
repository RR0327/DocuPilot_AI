# Phase 4 Step 3 — Classification refinement and independent evaluation

Copyright (c) 2026 Tech_Innovators · MIT License.

## Claims and limitations
- Bundled `backend/evaluation/classification_cases.json` is **synthetic** regression data, not an independent validation dataset.
- `backend/evaluation/independent_labels_TEMPLATE.json` is a **template only**; its placeholder is not an authentic independent dataset. Replace placeholders with licensed/consented text and genuinely independently assessed labels.
- The external evaluation command requires a provenance declaration. It checks metadata presence, **not the truth** of independence claims. For meaningful performance claims use a distinct, held-out, representative corpus with documented sampling, license, blind labeling and disagreement adjudication.
- Bangla heuristic signals and targeted OCR alternatives are deterministic. No trained multilingual model or calibrated probabilities are introduced.
- Page text and the original extracted document remain unchanged by reclassification. OCR evidence is page-linked text; spatial bounding boxes are not invented.

## Windows 11 PowerShell — backend (repository root)
```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
cd backend
python manage.py check
python manage.py migrate
python manage.py makemigrations --check --dry-run
python manage.py test core.test_classification_refinement core.test_classification_evaluation core.test_classification --verbosity 2
python manage.py test --verbosity 2
python manage.py evaluate_classification --output synthetic_classification_report.json
# AFTER you have an independently reviewed, licensed dataset:
python manage.py evaluate_classification --dataset evaluation/independent_labels.json --output independent_classification_report.json
```
The last command requires you to create the genuine `backend/evaluation/independent_labels.json` first. It is NOT bundled. The report includes provenance, macro scores, error buckets, matrix and per-case evidence checks.

## Windows 11 PowerShell — frontend (repository root, separate terminal)
```powershell
cd frontend
npm install
npm test
npx playwright install chromium
npm run test:e2e
npm run build
npm run dev
```

## Manual checks
1. Upload and extract English documents covering invoice/policy/report/contract and an unrelated note; verify page-grounded evidence and `unknown` abstention.
2. Upload consented Bangla samples (চালান নম্বর / গোপনীয়তা নীতি / গবেষণা পদ্ধতি / এই চুক্তি) and verify evidence excerpts exactly appear in extracted pages.
3. Try a scanned document with OCR confusion `Inv0ice No` and check that an actual source excerpt appears, not a fabricated correction.
4. Confirm reclassification is owner-scoped, anonymous and cross-owner requests are denied, and active extraction conflicts remain blocked.
5. Confirm the Classification Quality UI still labels bundled metrics as synthetic and shows false abstentions / unsafe guesses.
6. Verify existing Celery/Redis, invoice review, supplier analytics, PDF evidence and hybrid Q&A functionality.

## Release decision
A passing synthetic regression suite supports demo stability only. Independent performance measurement is pending until a real dataset is provided and assessed.
