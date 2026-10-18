# Phase 5 Step 2 — Authentication & API Security Acceptance

Tech_Innovators · SQLite3 · Django Session Authentication.

## Migration and compatibility

1. Back up `.env`, `backend/db.sqlite3` and `backend/private_media` before upgrading.
2. Run `python manage.py migrate` to apply `core.0012_authenticationfailure`.
3. Old HTTP Basic clients are **not** supported by default. Existing browser users must sign in again using the session form. To temporarily run a **local only** legacy API test, set `DOCUPILOT_ALLOW_DEV_BASIC=true` and `DJANGO_DEBUG=true` then restart Django. Never enable this on the Internet.
4. Your documents, passwords, data and previous sessions remain in SQLite3; the app now uses a CSRF-protected login endpoint and HttpOnly cookie.

## Windows 11 commands

From repository root in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
cd backend
python manage.py check
python manage.py migrate
python manage.py makemigrations --check --dry-run
python manage.py test core.test_auth_security core.test_release_security --verbosity 2
python manage.py test --verbosity 2
python manage.py release_check
python manage.py check --deploy
python manage.py runserver
```

In a second terminal from `frontend`:

```powershell
npm install
npm test
npx playwright install chromium
npm run test:e2e
npm run build
npm run dev
```

## Browser verification

- Visit `http://localhost:5173`. Log in with a Django user. Inspect the network request: POST `/api/auth/login/` carries CSRF header; authenticated `/api/documents/` requests must **not** have HTTP Authorization.
- Confirm the session cookie is HttpOnly and has `Secure` when configured behind HTTPS.
- Refresh the browser: session persists; after sign-out it is inaccessible.
- Submit wrong credentials until the configured threshold: expect 429 and `Retry-After`. Wait for the window or reset test DB.
- With a second account, request the first account's document, private PDF and classification history: expect 404.
- Validate session idle timeout and CSRF rejection of malicious POST.
- Check OCR, private PDF viewer, Q&A, invoice dashboard, human reviews, supplier analytics, Celery/Redis and classification workflows.

## Deployment gate

- Set `DJANGO_DEBUG=false`, generate a 50+ character secret key, use HTTPS, restrictive `DJANGO_ALLOWED_HOSTS`, correct proxy headers, and session cookies Secure.
- Never expose Django runserver directly to the Internet. Terminate TLS at a controlled reverse proxy. Do not trust spoofable X-Forwarded-For. Rate-limit by REMOTE_ADDR as seen by the application; ensure trusted proxy network topology and upstream request limits.
- Current controls reduce brute-force risk but do not replace external edge rate limiting and penetration testing. Auth rate-limit buckets persist in SQLite3 and can grow with unique clients; schedule cleanup and monitor database growth.
- Turn off `DOCUPILOT_ALLOW_DEV_BASIC`; run `python manage.py release_check` and `python manage.py check --deploy`. Review warnings; deploy remains blocked until all independent security gates pass.

## Expected results and known limitations

- Session login, CSRF and 429 responses; no Basic header on browser API; 35 frontend unit tests and complete backend suite passing.
- Phase 5 Step 2 does not add MFA or password reset. It does not certify security of reverse-proxy/TLS configuration.
- Existing SQLite3 and Tech_Innovators license remain unchanged.
