from django.contrib.auth import get_user_model
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from .models import Document, DocumentPage, DocumentChunk, QuestionAnswer
from .search import split_text, rebuild_document_chunks, retrieve
from .extraction import extract_document
from django.test import override_settings
import tempfile


class SearchTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.alice = User.objects.create_user(username="search_alice", password="test-password-123")
        self.bob = User.objects.create_user(username="search_bob", password="test-password-123")
        self.client = APIClient()
        self.doc = Document.objects.create(owner=self.alice, title="Refund policy", file_type="txt", processing_status="completed")
        DocumentPage.objects.create(document=self.doc, page_number=1, extracted_text="Refund requests are accepted within thirty days of purchase.")
        rebuild_document_chunks(self.doc)

    def test_split_preserves_exact_source_offsets(self):
        text = "This is a sentence. " * 90
        chunks = split_text(text, max_chars=100, overlap=20)
        self.assertGreater(len(chunks), 1)
        for start, end, content in chunks:
            self.assertEqual(content, text[start:end])
            self.assertLessEqual(end - start, 100)

    def test_answer_and_persist_source_provenance(self):
        self.client.force_authenticate(self.alice)
        response = self.client.post('/api/ask/', {'question': 'What is the refund policy?'}, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        payload = response.json()
        self.assertTrue(payload['has_evidence'])
        self.assertIn('Refund requests', payload['answer'])
        self.assertEqual(payload['source_references'][0]['page_number'], 1)
        self.assertEqual(payload['source_references'][0]['document_id'], self.doc.id)
        self.assertEqual(QuestionAnswer.objects.get(pk=payload['id']).owner, self.alice)

    def test_no_evidence_is_explicit_and_never_hallucinated(self):
        self.client.force_authenticate(self.alice)
        response = self.client.post('/api/ask/', {'question': 'What is the astrophysics launch code?'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['has_evidence'])
        self.assertEqual(response.json()['source_references'], [])
        self.assertIn('Insufficient evidence', response.json()['answer'])

    def test_isolation_and_explicit_document_restriction(self):
        self.client.force_authenticate(self.bob)
        self.assertFalse(self.client.post('/api/ask/', {'question': 'refund requests'}, format='json').json()['has_evidence'])
        self.assertEqual(self.client.post('/api/ask/', {'question': 'refund', 'document_ids': [self.doc.pk]}, format='json').status_code, 404)
        self.client.force_authenticate(self.alice)
        self.assertTrue(self.client.post('/api/ask/', {'question': 'refund', 'document_ids': [self.doc.pk]}, format='json').json()['has_evidence'])

    def test_invalid_inputs_and_unauthenticated(self):
        self.assertIn(self.client.post('/api/ask/', {'question': 'refund'}, format='json').status_code, (401, 403))
        self.client.force_authenticate(self.alice)
        for payload in ({}, {'question': '  '}, {'question': 10}, {'question': 'refund', 'document_ids': ['bad']}, {'question': 'x' * 501}):
            self.assertEqual(self.client.post('/api/ask/', payload, format='json').status_code, 400)

    def test_keyword_boundary_and_rebuild_idempotence(self):
        self.assertEqual(retrieve(self.alice, 'refunds'), [])
        rebuild_document_chunks(self.doc)
        self.assertEqual(DocumentChunk.objects.filter(document=self.doc).count(), 1)
        self.doc.processing_status = 'failed'
        self.doc.save(update_fields=['processing_status'])
        self.assertEqual(retrieve(self.alice, 'refund'), [])

    def test_re_extraction_rebuilds_chunks(self):
        with tempfile.TemporaryDirectory() as temp:
            with override_settings(MEDIA_ROOT=temp):
                doc = Document.objects.create(owner=self.alice, title='source', file_type='txt', file=SimpleUploadedFile('source.txt', b'Policy apples only'))
                extract_document(doc)
                self.assertTrue(retrieve(self.alice, 'apples'))
                with doc.file.open('wb') as stream:
                    stream.write(b'Policy oranges only')
                extract_document(doc)
                self.assertFalse(retrieve(self.alice, 'apples'))
                self.assertTrue(retrieve(self.alice, 'oranges'))
