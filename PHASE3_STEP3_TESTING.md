# Phase 3 Step 3 — Windows 11 verification

The synchronous document extraction endpoint is unchanged. **Async mode is opt-in**, requires Redis and a Celery worker, and stores its status in SQLite3. This is a development/demo deployment, not production-grade distributed job execution.

## Backup and setup

Before updating, back up `.env`, `backend/db.sqlite3`, and `backend/private_media/`. Keep the existing four root files named `LICENSE`, `CONTRIBUTING.md`, `README.md`, `SECURITY.md`.

Open PowerShell at the project root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements-async.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
cd backend
python manage.py check
python manage.py migrate
python manage.py makemigrations --check --dry-run
python manage.py test core.test_processing --verbosity 2
python manage.py test --verbosity 2
```

Expected: migration `core.0008_processingjob` applied, no uncommitted model changes, all new processing tests and full regression suite pass.

## Redis on Windows 11

Use **Docker Desktop with WSL 2** (recommended). Run from PowerShell:

```powershell
docker run --name docupilot-redis -p 127.0.0.1:6379:6379 -d redis:7-alpine redis-server --appendonly yes
docker exec docupilot-redis redis-cli ping
```

Expected: `PONG`. If container exists already, use `docker start docupilot-redis`. Do not expose port 6379 publicly or leave unauthenticated Redis accessible beyond localhost. A locally installed Redis inside WSL 2 is an alternative.

Edit the project root `.env`:

```dotenv
DOCUPILOT_ASYNC_ENABLED=true
DOCUPILOT_REDIS_URL=redis://127.0.0.1:6379/0
```

Start **three terminals**:

Backend terminal, working directory `backend/`:

```powershell
..\.venv\Scripts\Activate.ps1
python manage.py runserver
```

Worker terminal, working directory `backend/`:

```powershell
..\.venv\Scripts\Activate.ps1
celery -A config worker --loglevel=info --pool=solo --concurrency=1
```

Use `--pool=solo` on Windows. This runs jobs sequentially and avoids Celery prefork incompatibilities on native Windows. Keep one solo worker for the SQLite-based demo.

Frontend terminal, working directory `frontend/`:

```powershell
npm install
npm test
npx playwright install chromium
npm run test:e2e
npm run build
npm run dev
```

Expected: 21 Node unit tests pass, browser suite and Vite build succeed, UI available at `http://localhost:5173`.

## Manual extraction acceptance

1. Create two Django test users, and sign in as the first user.
2. Upload a 2-page text PDF or small scanned PDF. Use **Background extract**; expect a job in `queued` or `running` state.
3. Confirm `succeeded` and page/character counts, then view extracted pages. Confirm no duplicated page/chunk records.
4. Disable the worker, submit another document and observe the `queued` state. Restart worker and confirm completion.
5. Submit an invalid/unreadable PDF (only if backend upload validation accepts the file signature), or mock extraction failure in automated tests; verify `failed` with sanitized error and owner-only retry.
6. Log in as user two: GET `/api/processing-jobs/<uuid>/` and POST `/api/processing-jobs/<uuid>/retry/` must return 404 for user one's job.
7. Turn off `DOCUPILOT_ASYNC_ENABLED` and restart Django: async submission must return 503, while **Extract text** (sync) still works.
8. Reconfirm OCR, human review, analytics, invoice reports, private PDF evidence, and semantic/hybrid Q&A.

## API contracts

- `POST /api/documents/{id}/extract-async/` → 202 queued job, 409 if another job active, 503 if background processing disabled/broker unavailable.
- `GET /api/processing-jobs/{uuid}/` → owner-only job state and counts, never raw worker exception.
- `POST /api/processing-jobs/{uuid}/retry/` → 202 new attempt only if previous job failed.
- `POST /api/documents/{id}/extract/` → original synchronous extraction contract unchanged.

**Limits:** The task state records stage-level changes (queued, running, succeeded, failed), not exact percent progress. Workers are at-least-once systems; duplicate deliveries are guarded by state checks. SQLite is suitable for the single-worker demo; high-concurrency production needs a different persistence/concurrency design. An absent worker cannot be detected immediately: jobs remain queued until worker resumes or an operator intervenes. The model retains prior extraction failure safeguards. Do not use HTTP Basic over unencrypted public networks.
