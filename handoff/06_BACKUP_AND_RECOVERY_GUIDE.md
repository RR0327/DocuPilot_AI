# SQLite3 backup and disaster recovery guide

## Policy
Protect both `backend/db.sqlite3` and `backend/private_media`; database-only backup leaves document references unusable. Keep `.env` secrets separately in an approved secrets store. Never commit any of these artifacts. ZIP backups from the utility are **not encrypted**.

## Backup, verify and dry run (PowerShell at repository root)
```powershell
New-Item -ItemType Directory -Force backups
# Pause uploads and background workers for media/database consistency.
python scripts/backup_restore.py backup --archive backups/handoff_snapshot.backup.zip
python scripts/backup_restore.py verify --archive backups/handoff_snapshot.backup.zip
python scripts/backup_restore.py restore --archive backups/handoff_snapshot.backup.zip
```
The script snapshots SQLite3 using the online backup API, stores private media, writes SHA-256 entries, checks ZIP paths, and verifies SQLite integrity. Save backup out of reach of public static/media serving.

## Restore drill — isolated copy only
1. Provision a disposable copy of the application and verify its source version/migrations match the archive.
2. Stop Django, Celery and Redis-consuming workers in the **target** environment; ensure no target files are in use.
3. Confirm `backend/db.sqlite3` and `backend/private_media` do **not** exist in the disposable target (move any test data elsewhere; do not delete production data).
4. Execute:
```powershell
python scripts/backup_restore.py restore --archive backups/handoff_snapshot.backup.zip --apply --confirm-restore
cd backend
python manage.py check
python manage.py migrate
python manage.py release_acceptance
```
5. Start the isolated service; sign in to a known test account; verify document records correspond to private media; check a PDF and invoice; verify cross-user authorization.
6. Record checksums, backup time, restore duration, recovery point and responsible operator. Destroy the disposable recovery copy securely when done.

## Operational cautions
The backup script refuses overwriting an existing database or media location; do not bypass this safeguard. Archive SHA-256 detects accidental corruption but does **not** authenticate the archive against a malicious actor who can change the manifest; sign or otherwise protect backups externally. Apply your organization-specific encryption, retention, access controls, immutable storage and off-site replication. Schedule recurrent recovery drills and define RTO/RPO rather than claiming they are met untested.
