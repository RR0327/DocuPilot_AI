"""DocuPilot offline SQLite3 + private-media backup/verify/restore.

No dependencies outside Python stdlib. Stop API/Celery before restore. Backup uses
SQLite's online backup API for a consistent database snapshot. This is a local
operator utility, not a substitute for encrypted off-site disaster recovery.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sqlite3
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DATABASE = ROOT / 'backend' / 'db.sqlite3'
MEDIA = ROOT / 'backend' / 'private_media'
VERSION = 1

def digest(data):
    return hashlib.sha256(data).hexdigest()

def safe_files():
    if not MEDIA.exists():
        return []
    paths = []
    for path in sorted(MEDIA.rglob('*')):
        if path.is_symlink():
            raise ValueError('Symlinks cannot be backed up: ' + str(path))
        if path.is_file():
            paths.append((f'media/{path.relative_to(MEDIA).as_posix()}', path))
    return paths

def make_backup(destination):
    destination = Path(destination).resolve()
    if destination.exists():
        raise FileExistsError('Refusing to overwrite existing backup')
    if not DATABASE.is_file():
        raise FileNotFoundError('Missing SQLite3 database; migrate first')
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as t:
            temp_path = Path(t.name)
        source = sqlite3.connect(f'file:{DATABASE.as_posix()}?mode=ro', uri=True)
        target = sqlite3.connect(temp_path)
        try:
            source.backup(target)
            row = target.execute('PRAGMA integrity_check').fetchone()
            if row is None or row[0] != 'ok':
                raise ValueError('Database integrity check failed')
        finally:
            source.close()
            target.close()
        snapshot = temp_path.read_bytes()
        manifest = {'format': VERSION, 'files': {'database/db.sqlite3': digest(snapshot)}}
        files = []
        for key, path in safe_files():
            contents = path.read_bytes()
            manifest['files'][key] = digest(contents)
            files.append((key, contents))
        # Restrictive permissions where supported, no secrets in archive metadata.
        fd = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, 'wb') as out, zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('database/db.sqlite3', snapshot)
            for key, contents in files:
                z.writestr(key, contents)
            z.writestr('manifest.json', json.dumps(manifest, indent=2, sort_keys=True))
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    finally:
        if temp_path:
            temp_path.unlink(missing_ok=True)
    print(f'Created {destination} ({len(manifest["files"])} files). Treat as highly confidential; encrypt before off-site storage.')

def verify_archive(archive):
    archive = Path(archive).resolve()
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate ZIP entries')
        if 'manifest.json' not in names:
            raise ValueError('Missing backup manifest')
        manifest = json.loads(z.read('manifest.json'))
        files = manifest.get('files')
        if manifest.get('format') != VERSION or not isinstance(files, dict) or 'database/db.sqlite3' not in files:
            raise ValueError('Unsupported or incomplete backup')
        if set(names) != set(files) | {'manifest.json'}:
            raise ValueError('Unexpected or missing ZIP entries')
        for key, expected in files.items():
            path = PurePosixPath(key)
            if (path.is_absolute() or '..' in path.parts or '\\' in key or
                (not key.startswith('media/') and key != 'database/db.sqlite3') or
                len(path.parts) < 2):
                raise ValueError('Unsafe archive path: ' + key)
            if digest(z.read(key)) != expected:
                raise ValueError('Checksum mismatch: ' + key)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as temp:
                temp_path = Path(temp.name)
                temp.write(z.read('database/db.sqlite3'))
            conn = sqlite3.connect(f'file:{temp_path.as_posix()}?mode=ro', uri=True)
            try:
                if conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                    raise ValueError('Invalid SQLite3 snapshot')
            finally:
                conn.close()
        finally:
            if temp_path:
                temp_path.unlink(missing_ok=True)
    return len(files)

def restore(archive, *, apply=False):
    file_count = verify_archive(archive)
    if not apply:
        print(f'DRY RUN: {file_count} verified entries. Stop Django and Celery; rerun with --apply --confirm-restore to restore into an EMPTY data directory.')
        return
    if DATABASE.exists() or MEDIA.exists():
        raise FileExistsError('Refusing to overwrite existing database/media. Move them to a safe separate location first.')
    # Staged extraction, path-checked and checksum-verified before touching destination.
    with zipfile.ZipFile(archive) as z:
        with tempfile.TemporaryDirectory(prefix='docupilot_restore_') as tmp:
            staging = Path(tmp)
            manifest = json.loads(z.read('manifest.json'))
            for key in manifest['files']:
                dest = staging / key
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(z.read(key))
            DATABASE.parent.mkdir(parents=True, exist_ok=True)
            (staging/'database'/'db.sqlite3').replace(DATABASE)
            if (staging/'media').exists():
                (staging/'media').replace(MEDIA)
    print(f'Restored {file_count} entries. Run Django checks and verify owner access before reopening the service.')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    cmd=parser.add_subparsers(dest='action', required=True)
    for name in ('backup','verify','restore'):
        sub=cmd.add_parser(name)
        sub.add_argument('--archive', required=True, type=Path)
        if name=='restore':
            sub.add_argument('--apply', action='store_true')
            sub.add_argument('--confirm-restore', action='store_true')
    args=parser.parse_args()
    try:
        if args.action=='backup': make_backup(args.archive)
        elif args.action=='verify': print(f'PASS: {verify_archive(args.archive)} entries verified (SHA-256 and SQLite integrity).')
        else:
            if args.apply and not args.confirm_restore:
                parser.error('--apply requires --confirm-restore')
            restore(args.archive, apply=args.apply)
    except (OSError, ValueError, zipfile.BadZipFile, sqlite3.Error) as exc:
        parser.exit(1, 'ERROR: '+str(exc)+'\n')

if __name__ == '__main__': main()
