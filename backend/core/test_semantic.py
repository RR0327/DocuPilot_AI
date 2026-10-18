from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from .models import Document, DocumentPage, ChunkEmbedding
from .search import rebuild_document_chunks, retrieve
from .semantic import SemanticUnavailable, cosine


@override_settings(DOCUPILOT_EMBEDDING_MODEL='test-model', DOCUPILOT_SEMANTIC_MIN_SCORE=0.4)
class SemanticTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username='vector_owner', password='secure')
        self.other = User.objects.create_user(username='vector_other', password='secure')
        self.document = Document.objects.create(owner=self.owner, title='Billing policy', file_type='txt', processing_status='completed')
        DocumentPage.objects.create(document=self.document, page_number=1, extracted_text='Invoices must be paid before the deadline.')
        rebuild_document_chunks(self.document)
        self.secret = Document.objects.create(owner=self.other, title='Private other', file_type='txt', processing_status='completed')
        DocumentPage.objects.create(document=self.secret, page_number=1, extracted_text='Private confidential payment information.')
        rebuild_document_chunks(self.secret)
        self.client = APIClient()

    @staticmethod
    def fake_vectors(texts):
        return [[1.0, 0.0] if 'deadline' in text.lower() or 'settlement' in text.lower() else [0.0, 1.0] for text in texts]

    def test_cosine(self):
        self.assertEqual(cosine([1, 0], [0, 1]), 0)
        self.assertAlmostEqual(cosine([2, 0], [4, 0]), 1)
        self.assertEqual(cosine([], []), 0)

    @patch('core.semantic.encode_texts')
    def test_semantic_owner_scope_and_cache(self, encode):
        encode.side_effect = self.fake_vectors
        hits = retrieve(self.owner, 'settlement', mode='semantic')
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].document_id, self.document.id)
        self.assertEqual(hits[0].retrieval_method, 'semantic')
        self.assertEqual(ChunkEmbedding.objects.count(), 1)
        retrieve(self.owner, 'settlement', mode='semantic')
        self.assertEqual(ChunkEmbedding.objects.count(), 1)
        self.assertEqual(len(encode.call_args.args[0]), 1)  # query only on cache hit

    @patch('core.semantic.encode_texts')
    def test_hybrid_and_document_scope(self, encode):
        encode.side_effect = self.fake_vectors
        self.assertTrue(retrieve(self.owner, 'deadline', mode='hybrid', document_ids=[self.document.pk]))
        self.assertFalse(retrieve(self.other, 'settlement', mode='semantic', document_ids=[self.document.pk]))

    @patch('core.semantic.encode_texts')
    def test_api_validates_mode_and_rejects_other_owner(self, encode):
        encode.side_effect = self.fake_vectors
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.post('/api/ask/', {'question': 'deadline', 'mode': 'wrong'}, format='json').status_code, 400)
        self.assertEqual(self.client.post('/api/ask/', {'question': 'deadline', 'mode': 'semantic', 'document_ids': [self.secret.pk]}, format='json').status_code, 404)
        response = self.client.post('/api/ask/', {'question': 'settlement', 'mode': 'semantic'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['retrieval_mode'], 'semantic')
        self.assertEqual(response.json()['source_references'][0]['retrieval_method'], 'semantic')

    @patch('core.semantic.encode_texts', side_effect=SemanticUnavailable('model unavailable'))
    def test_unavailable_model_explicit_503_no_history(self, _encode):
        self.client.force_authenticate(self.owner)
        response = self.client.post('/api/ask/', {'question': 'deadline', 'mode': 'semantic'}, format='json')
        self.assertEqual(response.status_code, 503)
        self.assertIn('model unavailable', response.json()['detail'])

    @patch('core.semantic.encode_texts')
    def test_reindex_deletes_cached_vectors(self, encode):
        encode.side_effect = self.fake_vectors
        retrieve(self.owner, 'settlement', mode='semantic')
        self.assertEqual(ChunkEmbedding.objects.count(), 1)
        rebuild_document_chunks(self.document)
        self.assertEqual(ChunkEmbedding.objects.count(), 0)

    def test_keyword_still_works_without_embeddings(self):
        self.assertTrue(retrieve(self.owner, 'deadline'))
        self.assertFalse(retrieve(self.owner, 'settlement'))
