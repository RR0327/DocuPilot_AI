# Phase 3 Step 4 — Windows 11 Verification

## Preservation
Keep your existing `.env`, `backend/db.sqlite3`, and `backend/private_media` folder when applying this repository. Back up SQLite and private files together. Do not commit credentials or uploaded documents.

## Backend
From the project root in PowerShell:
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
python -m pip install -r backend/requirements-async.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
cd backend
python manage.py check
python manage.py migrate
python manage.py makemigrations --check --dry-run
python manage.py test core.test_processing core.test_recovery --verbosity 2
python manage.py test --verbosity 2
python manage.py recover_processing_jobs
python manage.py runserver
```
Expect migration `core.0009_processingjob_recovery`, no pending migrations, passing tests, and `DRY RUN` with stale-job counts.

## Redis and Celery
Install Docker Desktop / WSL2. Start Redis with:
```powershell
docker run --name docupilot-redis -p 127.0.0.1:6379:6379 -d redis:7-alpine
# If it exists already: docker start docupilot-redis
docker exec docupilot-redis redis-cli ping
```
Expect `PONG`. In project-root `.env`, set `DOCUPILOT_ASYNC_ENABLED=true`. From a fresh PowerShell terminal under `backend` with venv activated:
```powershell
celery -A config worker --loglevel=info --pool=solo --concurrency=1
```
Run with only one worker when using SQLite for the local demo. Synchronous extraction is available when async is disabled.

## Dry-run and recovery
```powershell
cd backend
python manage.py recover_processing_jobs --queued-minutes 30 --running-minutes 120
python manage.py recover_processing_jobs --apply --queued-minutes 30 --running-minutes 120 --max-requeues 2
```
**Caution:** Only apply recovery after inspecting the worker. Running jobs are marked failed, not requeued, because a worker may still process them. If an old worker later completes, examine its logs and outputs before retrying. A queued job re-dispatch uses the same idempotent UUID and has a bounded recovery count. The dry-run performs no database writes.

## UI and regression
From project-root `frontend`:
```powershell
npm install
npm test
npx playwright install chromium
npm run test:e2e
npm run build
npm run dev
```
Expected: all existing frontend tests pass, browser tests pass, and Vite build succeeds. Verify job polling, recovery attempt display, authorized job overview, previous upload/OCR, Q&A, review and supplier analytics.

## Security / reliability notes
- `GET /api/processing-jobs/overview/` requires login and shows only the user's own job counters.
- `GET /api/processing-jobs/{uuid}/` and retry continue to enforce ownership.
- No admin recovery endpoint is exposed to end users; management command requires local operator access.
- Celery/Redis and SQLite are suitable for local demonstration, not a multi-worker production guarantee.
- Recovery timeout is based on job timestamps, **not heartbeat**. Long OCR can exceed a threshold; use conservative values and inspect worker before `--apply`.
- Production release still requires supervised workers, monitoring, stronger authentication, backup/restore drills, and a more robust concurrency strategy.
