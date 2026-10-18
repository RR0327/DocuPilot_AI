"""Release-quality tests: source integrity, financial warnings and evaluation isolation."""
import json
from io import StringIO
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from .models import Document, DocumentPage
from .invoice_extraction import parse_invoice_pages
from .search import rebuild_document_chunks, retrieve
from .evaluation_metrics import check_source_excerpt


class Phase2QualityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='quality_user', password='test-value')

    def test_citation_exactly_matches_private_document_page(self):
        doc = Document.objects.create(owner=self.user, title='Policy', file_type='txt', processing_status='completed')
        DocumentPage.objects.create(document=doc, page_number=1, extracted_text='Refund requests are accepted within thirty days.')
        rebuild_document_chunks(doc)
        for hit in retrieve(self.user, 'refund'):
            self.assertTrue(check_source_excerpt(doc.pages.get(page_number=hit.page_number).extracted_text, hit.excerpt))

    def test_due_date_before_invoice_date_is_review_warning(self):
        page = DocumentPage(page_number=1, extracted_text='Invoice No: TEST-9\nInvoice Date: 2026-10-12\nDue Date: 2026-10-11')
        parsed = parse_invoice_pages([page])
        self.assertTrue(any('precedes' in message for message in parsed['warnings']))
        self.assertEqual(parsed['fields']['due_date'], '2026-10-11')

    def test_benchmark_reversible_and_keyword(self):
        before = Document.objects.count()
        stream = StringIO()
        call_command('evaluate_docupilot', stdout=stream)
        results = json.loads(stream.getvalue())
        self.assertEqual(results['retrieval']['recall_at_5'], 1.0)
        self.assertEqual(results['retrieval']['no_evidence_abstention_rate'], 1.0)
        self.assertEqual(results['retrieval']['citation_integrity_rate'], 1.0)
        self.assertEqual(results['invoice']['exact_match_rate'], 1.0)
        self.assertEqual(Document.objects.count(), before)
