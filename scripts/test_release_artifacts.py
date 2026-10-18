"""Offline release package hygiene checks with no Django dependencies."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class ReleaseArtifactTests(unittest.TestCase):
    def test_required_documents(self):
        for filename in ('README.md','LICENSE','CONTRIBUTING.md','SECURITY.md'):
            with self.subTest(filename=filename):
                self.assertTrue((ROOT/filename).is_file())
        self.assertIn('Tech_Innovators', (ROOT/'LICENSE').read_text(encoding='utf-8'))

    def test_sqlite_and_migration_compatibility(self):
        settings = (ROOT/'backend/config/settings.py').read_text(encoding='utf-8')
        self.assertIn('django.db.backends.sqlite3',settings)
        self.assertIn('MEDIA_URL = None',settings)
        migration=(ROOT/'backend/core/migrations/0006_invoicelineitem.py').read_text(encoding='utf-8')
        self.assertIn('unique_invoice_line_number',migration)
        self.assertIn('ordering',migration)

    def test_client_has_session_and_csrf_flow(self):
        code=(ROOT/'frontend/src/api.js').read_text(encoding='utf-8')
        self.assertIn('credentials: "same-origin"',code)
        self.assertIn('X-CSRFToken',code)
        self.assertIn('signOut',code)

    def test_ignore_private_files(self):
        contents=(ROOT/'.gitignore').read_text(encoding='utf-8')
        for item in ('.env','*.sqlite3','backend/private_media/','backups/'):
            self.assertIn(item,contents)

if __name__=='__main__': unittest.main()
