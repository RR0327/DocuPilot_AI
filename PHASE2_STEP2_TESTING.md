# Phase 2 Step 2 — Windows 11 test and acceptance guide

## Installation
From `DocuPilot_AI` root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
# Optional, required only for semantic/hybrid queries:
python -m pip install -r backend/requirements-semantic.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
cd backend
python manage.py check
python manage.py migrate
python manage.py makemigrations --check --dry-run
python manage.py test --verbosity 2
python manage.py runserver
```

Expected migration: `core.0005_chunkembedding`. Keyword mode remains usable without the optional installation. The first semantic request downloads the multilingual model; this may require Internet access, available disk space and several minutes. Later requests reuse the local model and SQLite chunk vectors. To enforce fully offline inference **after** the model is cached, set `DOCUPILOT_MODEL_OFFLINE=true` in `.env` and restart Django. The default model `intfloat/multilingual-e5-small` is used as an optional multilingual starter. Semantic quality and minimum score require evaluation on real Bangla/English documents; do not interpret similarity as confidence.

Open another terminal:

```powershell
cd frontend
npm install
npm test
npx playwright install chromium
npm run test:e2e
npm run build
npm run dev
```

Expected: all tests pass; development UI at `http://localhost:5173`.

## Manual end-to-end scenario
1. Sign in with a Django development account. Upload two PDF/TXT documents; run extraction.
2. In **Ask documents**, choose **Keyword** and ask a literal document phrase. Check exact source page.
3. Switch to **Semantic**, ask a paraphrase without the same words, and check evidence and mode metadata. First query may download model weights.
4. Switch to **Hybrid**, repeat and verify cross-document source references.
5. Select just one document; confirm no evidence from others is returned.
6. Sign in as a second user; confirm the first user's documents are invisible.
7. Re-extract a document, check its source content and ensure stale vector entries disappear.
8. With optional dependencies removed or model unavailable, verify keyword still succeeds and semantic reports HTTP 503.
9. Verify invoice extraction, CSV, OCR, backend tests, and frontend build still succeed.

## Caveats
- Retrieval is SQLite-based and scans at most 3000 owner-scoped chunks in semantic mode. Narrow scope for larger data. This is not a vector-index service.
- No generative model is used. Answers are quoted snippets and may not logically answer a question despite semantic similarity.
- Optional model dependencies can use substantial CPU, storage and memory on Windows.
- Model names/versions are stored with cached embeddings; chunk changes invalidate cached rows on deletion.
- Use only non-sensitive sample documents until authentication, TLS and deployment security are reviewed.
