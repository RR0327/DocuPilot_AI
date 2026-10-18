# Phase 5 Step 3 — final system integration and acceptance

## Baseline and user-provided changes
Built from the Phase 5 Step 2 complete repository. The following user-supplied **complete replacement files** were applied at their stated destinations:
- `backend/config/settings.py` (uploaded as `settings(1).py`; explicit `MEDIA_URL = None`)
- `backend/core/migrations/0006_invoicelineitem.py` (restores model ordering metadata)
- `frontend/e2e/mvp.spec.js` (session-based E2E mocks)
- `frontend/playwright.config.js` (uses installed **Chrome** browser channel)
- `scripts/backup_restore.py` (identical to Step 2 baseline; preserved user copy)

Existing deployed databases must not be reset. Model ordering is metadata-only and should not generate a new migration. `0006` must not be edited again after deployment without checking migration reproducibility.

## Windows 11 installation
1. Back up `.env`, `backend/db.sqlite3`, and `backend/private_media`; use `scripts/backup_restore.py backup` while document uploads/worker writes are paused.
2. From project root: `py -3.12 -m venv .venv` then `.\.venv\Scripts\Activate.ps1`.
3. `python -m pip install -r backend/requirements.txt`.
4. `cd backend`; run `python manage.py check`, `python manage.py migrate`, `python manage.py makemigrations --check --dry-run`.
5. Run `python manage.py test core.test_release_acceptance core.test_auth_security core.test_release_security --verbosity 2`.
6. Run `python manage.py test --verbosity 2`.
7. Run `python manage.py release_check` and `python manage.py release_acceptance --output ../release-reports/acceptance.json` (directory is gitignored). For production configuration, additionally run `python manage.py release_acceptance --require-production` and `python manage.py check --deploy`.
8. From project root: `python -m unittest discover -s scripts -p 'test_*.py' -v`.
9. Start Django (`python manage.py runserver`) from backend. In second terminal `cd frontend`, `npm install`, `npm test`, `npm run build`, `npm run test:e2e`, `npm run dev`.

**Important:** The uploaded Playwright configuration uses `channel: 'chrome'`: install Google Chrome for these tests. `npx playwright install chromium` alone does **not** provide the required Chrome stable channel. `npm run test:e2e` uses mocked API responses; execute the separate live-backend manual tests below.

## Backup and recovery drill (on a disposable copy only)
- Pause Django/Celery uploads/writes. `python scripts/backup_restore.py backup --archive backups/p5s3.backup.zip`.
- `python scripts/backup_restore.py verify --archive backups/p5s3.backup.zip`.
- `python scripts/backup_restore.py restore --archive backups/p5s3.backup.zip` performs a dry run.
- In an **isolated disposable installation with empty data paths**, perform `python scripts/backup_restore.py restore --archive backups/p5s3.backup.zip --apply --confirm-restore`.
- Confirm restored database, document owner isolation, private file integrity and a subsequent login. Do not restore over an occupied database or media tree. Backups are unencrypted and must be encrypted for off-site storage.

## Live end-to-end acceptance
- Create two ordinary non-staff accounts, upload a PDF and a TXT file as one account, verify page/OCR extraction, private PDF evidence, keyword Q&A, and optionally semantic/hybrid queries.
- Extract a sample invoice; verify line items, monetary mismatch warnings, review corrections, supplier analytics, CSV export and reconciliation.
- Classify invoice/policy/report/contract; verify unknown abstention, owner classification override, feedback and reliability dashboard.
- Test session login, logout, refresh, CSRF rejection, lockout, idle timeout and owner isolation across accounts.
- Optionally enable Redis/Celery; verify queued/running/succeeded/failed handling and operator-controlled recovery. Keep disabled if not installed.
- Confirm no `Authorization: Basic ...` header on ordinary frontend requests and no public URL for private media.

## Release decision
`release_acceptance` is a read-only **local preflight**, not external audit or penetration test. It checks route resolution, effective security settings, and outstanding migrations. It intentionally does not read private user data. Its JSON output contains no credentials, usernames, or document text.

**Local-demo gate:** all unit tests, full backend suite, browser mocked E2E, live user journey, backup/restore isolation, and cross-user tests pass. **Internet-facing production gate:** HTTPS, proper reverse proxy, edge rate limiting, secrets management, external security review, operational alerting, backups and independent classification evaluation are separately required. No production approval is implied by passing the local tests.
