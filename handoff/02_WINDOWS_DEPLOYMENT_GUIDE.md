# Windows 11 installation, demonstration and deployment guide

## Requirements
Windows 11, Python 3.12, current Node.js LTS/npm, Google Chrome (Playwright config uses `channel: "chrome"`), optional Tesseract for OCR, optional Redis/Celery for async extraction, optional semantic embedding dependencies. Use PowerShell in the extracted repository root. Make sure `.env` is private.

## First-time setup — Backend terminal
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
# Development only: .env may use DJANGO_DEBUG=true; never ship this secret.
cd backend
python manage.py check
python manage.py migrate
python manage.py makemigrations --check --dry-run
python manage.py test --verbosity 2
python manage.py release_acceptance
python manage.py runserver
```
Create a user once with `python manage.py createsuperuser` if appropriate. Do not replace an existing populated `db.sqlite3` while upgrading.

## Frontend terminal
```powershell
cd frontend
npm install
npm test
npm run build
npm run test:e2e
npm run dev
```
Open `http://127.0.0.1:5173`; Vite proxies `/api` to Django. Playwright's checked-in browser tests mock APIs and **do not replace** live backend user-journey tests. Install Google Chrome for this configuration.

## Optional capabilities
```powershell
# Backend environment, from repository root:
python -m pip install -r backend/requirements-semantic.txt
python -m pip install -r backend/requirements-async.txt
```
Enable `DOCUPILOT_ASYNC_ENABLED=true` and provide a reachable Redis broker only after installing/configuring a worker. From `backend/`: `celery -A config worker --pool=solo --concurrency=1 --loglevel=info`. Synchronous mode requires neither Redis nor Celery. Set `DOCUPILOT_TESSERACT_CMD` to installed Tesseract path if absent from PATH; install language data for Bangla OCR if needed.

## Security preflight
For a real TLS deployment configure a **unique random** `DJANGO_SECRET_KEY` (at least 50 characters), `DJANGO_DEBUG=false`, restricted `DJANGO_ALLOWED_HOSTS`, correct `DJANGO_CSRF_TRUSTED_ORIGINS`, secure cookies, TLS termination, reverse-proxy forwarding only if trusted. Check:
```powershell
cd backend
python manage.py check --deploy
python manage.py release_check
python manage.py release_acceptance --require-production
```
`runserver` is a local development server; use a supported production application server and reverse proxy only after the production gates are reviewed. Do not enable HSTS until stable HTTPS and ownership of subdomains are established. No public `MEDIA_URL` is allowed.

## Release verification and artifact handling
Run with real disposable accounts (owner A/owner B), test private PDF and API cross-user authorization, CSRF rejection, rate limiting, idle logout, invoice review, evidence Q&A, classification and optional workers. Use `07_FINAL_RELEASE_CHECKLIST.md` before any distribution. ZIP must exclude live data, `.env`, backups, local JS dependency trees and Python virtual environments.
