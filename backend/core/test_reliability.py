"""Authenticated owner isolation and privacy of reliability report."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from core.models import Document, DocumentClassification, ClassificationFeedback

class ReliabilityTests(TestCase):
    def setUp(self):
        U=get_user_model();self.owner=U.objects.create_user(username='r_owner',password='TestPass987!')
        self.other=U.objects.create_user(username='r_other',password='TestPass987!')
        self.client=APIClient()
    def test_anonymous_denied(self):
        self.assertIn(self.client.get('/api/classification/reliability/').status_code,(401,403))
    def test_owner_only_and_aggregate_only(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        document=Document.objects.create(owner=self.other,title='Sensitive private title',file=SimpleUploadedFile('r.txt',b'private'),file_type='txt')
        DocumentClassification.objects.create(document=document,category='invoice',evidence=[],scores={},reason='rule')
        ClassificationFeedback.objects.create(document=document,reviewer=self.other,action='override',category='contract',machine_category='invoice',note='secret note')
        self.client.force_authenticate(user=self.owner)
        res=self.client.get('/api/classification/reliability/')
        self.assertEqual(res.status_code,200)
        self.assertEqual(res.data['reviewed_document_count'],0)
        self.assertNotIn('Sensitive',str(res.data));self.assertNotIn('secret',str(res.data))
        self.assertEqual(res['Cache-Control'],'no-store')
