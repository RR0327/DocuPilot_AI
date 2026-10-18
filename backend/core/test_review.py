from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from .models import Document, ExtractedRecord, ExtractionReview
from .invoice_dashboard import serialize_invoice


class HumanReviewTests(TestCase):
    def setUp(self):
        user = get_user_model()
        self.owner = user.objects.create_user(username='review_owner', password='passABC123!')
        self.other = user.objects.create_user(username='review_other', password='passABC123!')
        doc = Document.objects.create(owner=self.owner, title='Private invoice', file_type='txt')
        self.record = ExtractedRecord.objects.create(document=doc, record_type='invoice', extracted_data={
            'fields': {'invoice_number': 'INV-001', 'total': '25.00'},
            'source_references': {'total': {'page_number': 2, 'excerpt': 'Total 25.00'}},
            'warnings': ['Check tax amount'], 'missing_fields': ['tax']})
        self.client = APIClient()

    def test_queue_is_owner_scoped_and_attention_flagged(self):
        self.client.force_authenticate(self.owner)
        result = self.client.get('/api/reviews/')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data['count'], 1)
        self.assertTrue(result.data['results'][0]['needs_attention'])
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get('/api/reviews/').data['count'], 0)
        self.assertEqual(self.client.get(f'/api/reviews/{self.record.pk}/').status_code, 404)

    def test_approve_preserves_original_and_writes_audit(self):
        self.client.force_authenticate(self.owner)
        result = self.client.post(f'/api/reviews/{self.record.pk}/', {'action': 'approve', 'corrections': {'total': '26.00'}, 'note': 'Compared original'}, format='json')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data['effective_fields']['total'], '26.00')
        self.assertEqual(result.data['original_fields']['total'], '25.00')
        self.assertEqual(result.data['source_references']['total']['page_number'], 2)
        self.record.refresh_from_db()
        self.assertEqual(self.record.validation_status, 'valid')
        self.assertEqual(self.record.extracted_data['fields']['total'], '25.00')
        self.assertEqual(ExtractionReview.objects.count(), 1)
        self.assertEqual(serialize_invoice(self.record)['total'], '26.00')

    def test_reopen_and_review_history(self):
        self.client.force_authenticate(self.owner)
        endpoint = f'/api/reviews/{self.record.pk}/'
        self.client.post(endpoint, {'action': 'approve', 'corrections': {'total': '26.00'}}, format='json')
        self.assertEqual(self.client.post(endpoint, {'action': 'approve'}, format='json').status_code, 400)
        reopened = self.client.post(endpoint, {'action': 'reopen'}, format='json')
        self.assertEqual(reopened.status_code, 200)
        self.assertEqual(reopened.data['effective_fields']['total'], '25.00')
        self.record.refresh_from_db()
        self.assertEqual(serialize_invoice(self.record)['total'], '25.00')
        rejected = self.client.post(endpoint, {'action': 'reject', 'note': 'Incorrect supplier'}, format='json')
        self.assertEqual(rejected.status_code, 200)
        self.assertEqual(rejected.data['validation_status'], 'invalid')
        self.assertEqual(len(rejected.data['history']), 3)

    def test_validation_rejects_bad_money_dates_and_empty_reason(self):
        self.client.force_authenticate(self.owner)
        endpoint = f'/api/reviews/{self.record.pk}/'
        for payload in (
            {'action': 'reject'},
            {'action': 'approve', 'corrections': {'total': '-1'}},
            {'action': 'approve', 'corrections': {'invoice_date': '2026-99-20'}},
            {'action': 'approve', 'corrections': {'evil': 'x'}},
            {'action': 'approve', 'corrections': {'total': '=SUM(A1:A2)'}},
        ):
            self.assertEqual(self.client.post(endpoint, payload, format='json').status_code, 400)
        self.assertEqual(ExtractionReview.objects.count(), 0)

    def test_anonymous_and_other_users_cannot_review(self):
        endpoint = f'/api/reviews/{self.record.pk}/'
        self.assertIn(self.client.post(endpoint, {'action': 'approve'}, format='json').status_code, (401,403))
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.post(endpoint, {'action': 'approve'}, format='json').status_code, 404)

    def test_invalid_filter(self):
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.get('/api/reviews/?status=arbitrary').status_code, 400)
