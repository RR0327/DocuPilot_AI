"""Offline backup regression tests (stdlib, isolated temporary directories)."""
import importlib.util
import json
import sqlite3
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('docupilot_backup',Path(__file__).with_name('backup_restore.py'))
b=importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

class BackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.database=self.root/'db.sqlite3'
        self.media=self.root/'private_media'
        self.media.mkdir()
        self.original=(b.DATABASE,b.MEDIA)
        b.DATABASE=self.database
        b.MEDIA=self.media
        self.addCleanup(self.restore_paths)
        c=sqlite3.connect(self.database)
        c.execute('CREATE TABLE important (message TEXT)')
        c.execute('INSERT INTO important VALUES (?)',('preserved',))
        c.commit()
        c.close()
        (self.media/'sample.txt').write_text('private document')
        self.archive=self.root/'snapshot.backup.zip'

    def restore_paths(self):
        b.DATABASE,b.MEDIA=self.original

    def test_backup_verify_and_non_destructive_restore(self):
        b.make_backup(self.archive)
        self.assertEqual(b.verify_archive(self.archive),2)
        with self.assertRaises(FileExistsError):
            b.restore(self.archive,apply=True)
        b.restore(self.archive)
        self.database.unlink()
        (self.media/'sample.txt').unlink()
        self.media.rmdir()
        b.restore(self.archive,apply=True)
        self.assertEqual((self.media/'sample.txt').read_text(),'private document')
        c=sqlite3.connect(self.database)
        self.assertEqual(c.execute('SELECT message FROM important').fetchone()[0],'preserved')
        c.close()

    def test_tampered_hash_is_rejected(self):
        b.make_backup(self.archive)
        with zipfile.ZipFile(self.archive,'a') as z:
            z.writestr('unexpected-file.txt','private')
        with self.assertRaises(ValueError):
            b.verify_archive(self.archive)

    def test_refuse_overwrite_existing_backup(self):
        b.make_backup(self.archive)
        with self.assertRaises(FileExistsError):
            b.make_backup(self.archive)

if __name__=='__main__': unittest.main()
