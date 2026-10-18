"""Phase 4 explainable classification, persistence, workflow and privacy tests."""
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient
from .classification import classify_pages, classify_document
from .models import Document, DocumentPage, DocumentClassification, ProcessingJob


class ClassifierRuleTests(TestCase):
    def test_four_categories_have_traceable_evidence(self):
        examples = {
            'invoice': 'Invoice No: 42\nInvoice Date: 2026-10-01\nSubtotal: 90',
            'policy': 'Privacy Policy\nPolicy Scope: All users.\nEffective date: today.',
            'report': 'Executive Summary\nMethodology\nFindings\nConclusions',
            'contract': 'This Agreement is between two parties.\nGoverning Law\nTermination Clause',
        }
        for expected, text in examples.items():
            with self.subTest(expected=expected):
                label, evidence, scores, reason = classify_pages([(3, text)])
                self.assertEqual(label, expected)
                self.assertTrue(any(e['category'] == expected and e['page_number'] == 3 for e in evidence))
                self.assertGreaterEqual(scores[expected], 3)

    def test_ambiguous_and_unrelated_documents_abstain(self):
        self.assertEqual(classify_pages([(1, 'Hello, how are you?')])[0], 'unknown')
        self.assertEqual(classify_pages([(1, 'Invoice No: 9 Privacy Policy')])[0], 'unknown')

    def test_no_filename_signal_and_evidence_limited(self):
        self.assertEqual(classify_pages([(1, 'Contract example without specific clauses')])[0], 'unknown')
        label, evidence, _, _ = classify_pages([(i, 'Executive Summary Methodology Findings Conclusions') for i in range(100)])
        self.assertEqual(label, 'report')
        self.assertLessEqual(len(evidence), 12)


class ClassificationAPITests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user('owner_classifier', password='test-pass')
        self.other = User.objects.create_user('other_classifier', password='test-pass')
        self.document = Document.objects.create(owner=self.owner, title='Untitled', file_type='txt',
            file=SimpleUploadedFile('document.txt', b'Invoice No: 42\nInvoice Date: 2026-10-01\nSubtotal: 90'))
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)
        self.url = f'/api/documents/{self.document.pk}/classification/'

    def test_auto_classify_on_extraction_and_repeat_is_idempotent(self):
        for _ in range(2):
            response = self.client.post(f'/api/documents/{self.document.pk}/extract/')
            self.assertEqual(response.status_code, 200)
        result = self.client.get(self.url)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data['category'], 'invoice')
        self.assertIsNone(result.data['calibrated_confidence'])
        self.assertTrue(result.data['evidence'])
        self.assertEqual(DocumentClassification.objects.filter(document=self.document).count(), 1)
        listing = self.client.get('/api/documents/')
        entries = listing.data['results'] if isinstance(listing.data, dict) else listing.data
        self.assertEqual(entries[0]['classification_category'], 'invoice')

    def test_reclassify_uses_stored_page_text(self):
        DocumentPage.objects.create(document=self.document, page_number=1, extracted_text='Governing Law. This Agreement. Termination Clause.')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['category'], 'contract')
        self.assertIn('Governing Law', self.document.pages.first().extracted_text)
        self.assertEqual(self.client.get(self.url).data['category'], 'contract')

    def test_empty_pages_and_busy_processing_rejected(self):
        self.assertEqual(self.client.post(self.url).status_code, 409)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        DocumentPage.objects.create(document=self.document, page_number=1, extracted_text='Annual report')
        ProcessingJob.objects.create(document=self.document, state='queued')
        self.assertEqual(self.client.post(self.url).status_code, 409)

    def test_cross_owner_and_anonymous_cannot_read_or_reclassify(self):
        DocumentPage.objects.create(document=self.document, page_number=1, extracted_text='Annual Report')
        classify_document(self.document)
        self.client.force_authenticate(user=self.other)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.post(self.url).status_code, 404)
        self.client.force_authenticate(user=None)
        self.assertIn(self.client.get(self.url).status_code, (401, 403))
        self.assertIn(self.client.post(self.url).status_code, (401, 403))
