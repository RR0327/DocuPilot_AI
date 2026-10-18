from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from .models import Document, DocumentClassification, ClassificationFeedback
from .feedback_quality import analyze_feedback, make_private_label_export


class FeedbackQualityTests(TestCase):
    def setUp(self):
        U = get_user_model()
        self.owner = U.objects.create_user('quality_owner',password='secret')
        self.other = U.objects.create_user('quality_other',password='secret')
        self.document = Document.objects.create(owner=self.owner,title='Secret Supplier Name',file_type='txt')
        DocumentClassification.objects.create(document=self.document,category='invoice',evidence=[{'excerpt':'Private data'}])
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)

    def decision(self, action, label):
        return ClassificationFeedback.objects.create(document=self.document,reviewer=self.owner,
            machine_category='invoice',category=label,action=action,note='TOP SECRET 123')

    def test_empty_review_counts_and_no_division_by_zero(self):
        r=self.client.get('/api/classification/feedback-quality/')
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.data['reviewed_document_count'],0)
        self.assertIsNone(r.data['agreement_rate'])

    def test_latest_review_only_and_clear_exclusion(self):
        self.decision('verify','invoice')
        self.decision('override','contract')
        r=self.client.get('/api/classification/feedback-quality/')
        self.assertEqual(r.data['disagreement_count'],1)
        self.assertEqual(r.data['agreement_count'],0)
        self.assertEqual(r.data['coverage_rate'],1.0)
        self.decision('clear','')
        r=self.client.get('/api/classification/feedback-quality/')
        self.assertEqual(r.data['reviewed_document_count'],0)

    def test_export_requires_explicit_opt_in_and_has_no_content(self):
        self.decision('override','contract')
        denied=self.client.post('/api/classification/feedback-label-export/',{},format='json')
        self.assertEqual(denied.status_code,400)
        r=self.client.post('/api/classification/feedback-label-export/',{'confirm_label_only_export':True},format='json')
        self.assertEqual(r.status_code,200)
        self.assertFalse(r.data['independent_ground_truth'])
        self.assertEqual(r.data['sample_count'],1)
        self.assertEqual(r['Cache-Control'],'no-store')
        payload=str(r.data)
        for secret in ('Secret Supplier Name','TOP SECRET','Private data','quality_owner'):
            self.assertNotIn(secret,payload)
        self.assertEqual(set(r.data['cases'][0]),{'sample_id','machine_label_at_review','human_label','review_action'})
        again=self.client.post('/api/classification/feedback-label-export/',{'confirm_label_only_export':True},format='json')
        self.assertNotEqual(again.data['cases'][0]['sample_id'],r.data['cases'][0]['sample_id'])

    def test_owner_isolation_and_unauthenticated_denial(self):
        self.decision('override','contract')
        self.client.force_authenticate(user=self.other)
        report=self.client.get('/api/classification/feedback-quality/')
        self.assertEqual(report.data['document_count'],0)
        export=self.client.post('/api/classification/feedback-label-export/',{'confirm_label_only_export':True},format='json')
        self.assertEqual(export.data['sample_count'],0)
        self.client.force_authenticate(user=None)
        for method,path in [('get','/api/classification/feedback-quality/'),('post','/api/classification/feedback-label-export/')]:
            self.assertIn(getattr(self.client,method)(path).status_code,(401,403))

    def test_original_machine_snapshot_not_mutable_current_prediction(self):
        self.decision('override','contract')
        DocumentClassification.objects.filter(document=self.document).update(category='policy')
        report=analyze_feedback(Document.objects.filter(owner=self.owner))
        self.assertEqual(report['confusion_matrix']['invoice']['contract'],1)
        self.assertEqual(report['machine_changed_since_decision_count'],1)
