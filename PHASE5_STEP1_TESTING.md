# DocuPilot AI — Phase 5 Step 1: Security and Recovery Acceptance

Owner: Tech_Innovators | Database: SQLite3 only | Scope: Release baseline, **not** authorization for public deployment.

## A. Windows 11 preparation

Back up `backend/db.sqlite3`, `backend/private_media`, and the root `.env` before replacing project files. Do not commit these files or use a sample `.env` as a production secret. Ensure Python 3.12, Node.js 20+, Tesseract, and (only if async mode is enabled) Redis + Celery solo worker are installed. For a local demo, keep `DJANGO_DEBUG=true` and `DOCUPILOT_ASYNC_ENABLED=false` unless testing async separately.

From the repository root, open **PowerShell**:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
cd backend
python manage.py check
python manage.py migrate
python manage.py makemigrations --check --dry-run
python manage.py release_check
python manage.py test core.test_release_security --verbosity 2
python manage.py test --verbosity 2
python manage.py check --deploy
```

`check --deploy` can warn in local development because localhost lacks HTTPS/HSTS; it is a production hardening report, not a reason to enable unsafe proxy trust or HSTS on localhost. Test `DJANGO_DEBUG=false` with the real production domain and TLS termination **before** publicly deploying. Use `python manage.py release_check` again in the deployment environment.

From the root in a new terminal:

```powershell
cd frontend
npm install
npm test
npx playwright install chromium
npm run test:e2e
npm run build
```

The Playwright contract suite uses mocked API routes: run a **separate** manual integration pass against a real Django instance, including distinct Alice/Bob accounts.

## B. Backup and restore drill (Python standard library)

Use a dedicated confidential backup folder, preferably on an encrypted local disk. Run from the repository root while the populated database still exists:

```powershell
python scripts/backup_restore.py backup --archive backups/docupilot_snapshot.backup.zip
python scripts/backup_restore.py verify --archive backups/docupilot_snapshot.backup.zip
python -m unittest discover -s scripts -p "test_*.py" -v
python scripts/backup_restore.py restore --archive backups/docupilot_snapshot.backup.zip
```

The last line is a **dry-run only**. To test a real restore, use a throwaway copy of the entire repository with the original DB and `private_media` moved to a secure external location. Stop Django and Celery. In that disposable copy, ensure `backend/db.sqlite3` and `backend/private_media` are **absent**, then run:

```powershell
python scripts/backup_restore.py restore --archive backups/docupilot_snapshot.backup.zip --apply --confirm-restore
cd backend
python manage.py check
python manage.py migrate --check
```

Validate the restored document count and owner authorization manually. **Never run `--apply` on your live installation.** The tool refuses to overwrite an existing DB or private media folder. Backup ZIPs contain unencrypted confidential documents and database contents; encrypt them, restrict filesystem permissions and do not send them to public storage. `.env` is intentionally excluded; back it up separately in a secrets manager.

## C. Production baseline

- Configure a new, random `DJANGO_SECRET_KEY` of at least 50 characters; set `DJANGO_DEBUG=false`.
- Use a domain-specific `DJANGO_ALLOWED_HOSTS` without wildcards and terminate TLS at a controlled HTTPS reverse proxy.
- `DJANGO_SECURE_SSL_REDIRECT=true`; secure session and CSRF cookies are configured automatically when DEBUG is false. Enable proxy HTTPS trust **only** if the controlled reverse proxy strips and sets `X-Forwarded-Proto`.
- Keep `DJANGO_HSTS_SECONDS=0` until the domain has working HTTPS and subdomain policies have been reviewed. Only then introduce HSTS deliberately.
- Do not expose `backend/private_media` as public static content or add permissive CORS settings.
- Restrict SQL database/backup directory permissions. Keep Redis bound to localhost or a private network with suitable authentication when remote.
- Do not use Django's `runserver` as a production WSGI/ASGI host. Use a supported production server and reverse proxy.
- Existing HTTP Basic authentication and lack of endpoint rate limiting remain **production blockers** for Internet-facing deployments without compensating protections. Do not claim an approved public security posture.
- Classifier synthetic benchmark results and owner feedback agreement are not independently measured production accuracy. Record the status of any genuine adjudicated dataset.

## D. Real integration acceptance (two accounts)

1. Anonymous API request cannot retrieve `/api/documents/`, review history, analytics, or private PDFs.
2. Alice uploads a PDF and a scanned page; verify OCR, source page evidence, Q&A, and owner-private viewer.
3. Bob cannot open Alice's documents, invoices, review history, jobs, or classification labels.
4. Verify invoice extraction, source-linked line items, human correction, supplier analytics and CSV.
5. Test keyword retrieval; where optional model is installed, semantic and hybrid. Confirm evidence excerpts match actual stored pages.
6. Confirm classification, unknown-case handling, review override history, and reliability/feedback reports.
7. Optional Redis/Celery: run queued extraction, failed-job recovery dry-run, duplicate-job behavior and polling.
8. Verify backup, archive tamper rejection and isolated restoration. Confirm no backup/archive was written inside publicly served frontend directories.
9. Run full Django tests, frontend unit tests, Playwright and production build on Windows.
10. Record unresolved threats, independent-evaluation status, test results, target environment and release approver in your own acceptance record.

**Acceptance:** a local-demo signoff may be issued after all applicable checks pass. **Public production release remains blocked** until Internet-facing authentication/rate limiting, TLS, ops, and an independent security review are completed.
