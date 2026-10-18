from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from .models import Document, DocumentPage, DocumentClassification, ClassificationFeedback, ProcessingJob
from .classification import classify_document


class ClassificationFeedbackTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user('review_cat_owner', password='password')
        self.other = User.objects.create_user('review_cat_other', password='password')
        self.doc = Document.objects.create(owner=self.owner, title='Invoice', file_type='txt')
        DocumentPage.objects.create(document=self.doc, page_number=1, extracted_text='Invoice No: 20 Invoice Date: 2026-10-18 Subtotal: 45')
        classify_document(self.doc)
        self.url = f'/api/documents/{self.doc.pk}/classification-review/'
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)

    def test_verify_and_clear_preserve_machine_and_history(self):
        response = self.client.post(self.url, {'action':'verify'}, format='json')
        self.assertEqual(response.status_code,201)
        self.assertEqual(response.data['effective_category'], 'invoice')
        self.assertEqual(response.data['verified_category'], 'invoice')
        response = self.client.post(self.url, {'action':'clear'}, format='json')
        self.assertEqual(response.status_code,201)
        self.assertEqual(response.data['review_status'], 'unreviewed')
        self.assertEqual(len(response.data['history']),2)
        self.assertEqual(DocumentClassification.objects.get(document=self.doc).category,'invoice')

    def test_override_keeps_original_evidence_even_after_reclassification(self):
        original = self.client.get(self.url).data['source_evidence']
        response = self.client.post(self.url, {'action':'override', 'category':'contract','note':'Manually checked'},format='json')
        self.assertEqual(response.status_code,201)
        self.assertEqual(response.data['effective_category'],'contract')
        self.assertEqual(response.data['machine_category'],'invoice')
        self.assertEqual(response.data['source_evidence'],original)
        self.assertEqual(self.client.post(f'/api/documents/{self.doc.pk}/classification/').status_code,200)
        self.assertEqual(self.client.get(self.url).data['effective_category'],'contract')
        self.assertEqual(ClassificationFeedback.objects.count(),1)

    def test_invalid_feedback_and_conflicts(self):
        for body in ({'action':'override','category':'invoice','note':'x'}, {'action':'override','category':'report'},
                     {'action':'verify','category':'contract'}, {'action':'clear','category':'invoice'},
                     {'action':'verify','evil':'unexpected'}):
            with self.subTest(body=body):
                self.assertEqual(self.client.post(self.url,body,format='json').status_code,400)
        ProcessingJob.objects.create(document=self.doc,state='running')
        self.assertEqual(self.client.post(self.url, {'action':'verify'},format='json').status_code,409)

    def test_owner_permissions_and_summary_isolation(self):
        self.client.post(self.url, {'action':'override','category':'policy','note':'Reviewed'}, format='json')
        own = self.client.get('/api/classification/feedback-evaluation/')
        self.assertEqual(own.status_code,200)
        self.assertEqual(own.data['counts']['overridden'],1)
        self.client.force_authenticate(user=self.other)
        self.assertEqual(self.client.get(self.url).status_code,404)
        self.assertEqual(self.client.post(self.url,{'action':'verify'},format='json').status_code,404)
        other = self.client.get('/api/classification/feedback-evaluation/')
        self.assertEqual(other.data['document_count'],0)
        self.client.force_authenticate(user=None)
        self.assertIn(self.client.get(self.url).status_code,(401,403))
        self.assertIn(self.client.get('/api/classification/feedback-evaluation/').status_code,(401,403))
