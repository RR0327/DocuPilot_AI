# Testing evidence index — reproducible claims only

## Evidence classification
- **User-reported:** user reports 20/20 acceptance checks passed for Phase 5 Step 3. This handoff does not contain signed raw Windows test logs. Treat this as a declaration requiring retained records for audit.
- **Re-run in this package build:** `npm test`, offline `unittest`, Python compile, ZIP integrity, baseline preservation. See `08_BUILD_MANIFEST.md` for measured outputs.
- **Pending independent proof:** external security testing, real-domain TLS deployment, unattended recovery rehearsal, independently adjudicated representative classification corpus.

## Commands and private evidence locations
| Evidence ID | Test | Command | Suggested redacted attachment (not embedded) |
|---|---|---|---|
| BE-01 | Django configuration | `python manage.py check` | `backend-check.txt` |
| BE-02 | All migrations applied | `python manage.py migrate` and `makemigrations --check --dry-run` | `migration-check.txt` |
| BE-03 | Acceptance + authentication regression | `python manage.py test core.test_release_acceptance core.test_auth_security -v 2` | `auth-acceptance-tests.txt` |
| BE-04 | Entire Django suite | `python manage.py test -v 2` | `backend-regression.txt` |
| BE-05 | Local and production release gate | `python manage.py release_acceptance` / `--require-production` | Redacted JSON report |
| FE-01 | JS units | `npm test` | `frontend-units.txt` |
| FE-02 | Browser mocked E2E | `npm run test:e2e` | `playwright-summary.txt` |
| FE-03 | Production bundle | `npm run build` | `vite-build.txt` |
| OP-01 | Backup archive check | `python scripts/backup_restore.py verify --archive ...` | checksum/integrity output |
| OP-02 | Isolated restore | `restore --apply --confirm-restore` in disposable copy | recovery checklist and redacted timestamps |
| SEC-01 | Owner A vs B | manual requests with separate accounts | redacted 401/403/404 evidence |
| ML-01 | Real labeled evaluation | `evaluate_adjudicated_classification` after genuine review | aggregated evaluation JSON |

## Evidence handling
Store test output in a local restricted folder outside Git; redact usernames, filenames, private document text, tokens, session cookies and filesystem paths that identify users. Do not embed real documents or restore archives inside repository ZIP. Screenshots should use fabricated demo content. Sign/date a release log with tested commit/archive SHA-256 when available.
