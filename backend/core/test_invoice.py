from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .invoice_extraction import parse_invoice_pages
from .models import Document, DocumentPage, ExtractedRecord


class InvoiceExtractionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.alice = User.objects.create_user(username='inv_alice', password='test-password-123')
        self.bob = User.objects.create_user(username='inv_bob', password='test-password-123')
        self.client = APIClient()
        self.document = Document.objects.create(owner=self.alice, title='Invoice', processing_status='completed', file_type='txt')
        DocumentPage.objects.create(document=self.document, page_number=1, extracted_text=(
            'Supplier: Example Ltd\nInvoice No: INV-2026-014\nInvoice Date: 2026-10-12\n'
            'Due Date: 2026-11-11\nSubtotal: BDT 200.00\nTax: BDT 30.00\nTotal Amount: BDT 230.00'
        ))

    def url(self):
        return f'/api/documents/{self.document.pk}/invoice/extract/'

    def test_extract_invoice_with_evidence_and_types(self):
        self.client.force_authenticate(self.alice)
        response = self.client.post(self.url())
        self.assertEqual(response.status_code, 201, response.content)
        payload = response.json()
        self.assertEqual(payload['record_type'], 'invoice')
        self.assertEqual(payload['validation_status'], 'unreviewed')
        data = payload['extracted_data']
        self.assertEqual(data['fields']['invoice_number'], 'INV-2026-014')
        self.assertEqual(data['fields']['total'], '230.00')
        self.assertEqual(data['fields']['currency'], 'BDT')
        self.assertEqual(data['fields']['due_date'], '2026-11-11')
        self.assertEqual(data['source_references']['total']['page_number'], 1)
        self.assertEqual(self.client.get('/api/invoices/').json()[0]['document_id'], self.document.id)

    def test_missing_values_never_guessed(self):
        page = DocumentPage.objects.get(document=self.document)
        page.extracted_text = 'Invoice No: XYZ-44'
        page.save()
        self.client.force_authenticate(self.alice)
        response = self.client.post(self.url())
        self.assertEqual(response.status_code, 201)
        data = response.json()['extracted_data']
        self.assertIsNone(data['fields']['total'])
        self.assertIn('total', data['missing_fields'])

    def test_rejects_absent_evidence_and_unprocessed_documents(self):
        self.document.processing_status = 'pending'
        self.document.save()
        self.client.force_authenticate(self.alice)
        self.assertEqual(self.client.post(self.url()).status_code, 422)
        self.assertEqual(ExtractedRecord.objects.count(), 0)

    def test_owner_isolation(self):
        self.client.force_authenticate(self.bob)
        self.assertEqual(self.client.post(self.url()).status_code, 404)
        self.assertEqual(self.client.get('/api/invoices/').json(), [])
        self.client.force_authenticate(user=None)
        self.assertIn(self.client.get('/api/invoices/').status_code, (401, 403))

    def test_does_not_infer_money_from_tax_percent(self):
        page = DocumentPage.objects.get(document=self.document)
        page.extracted_text = 'Invoice No: A1\nVAT: 15%'
        page.save()
        data = parse_invoice_pages([page])
        self.assertIsNone(data['fields']['tax'])

    def test_total_is_not_subtotal(self):
        page = DocumentPage.objects.get(document=self.document)
        page.extracted_text = 'Invoice No: B2\nSubtotal: 100.00'
        page.save()
        data = parse_invoice_pages([page])
        self.assertIsNone(data['fields']['total'])

    def test_conflicting_totals_trigger_warning(self):
        page = DocumentPage.objects.get(document=self.document)
        page.extracted_text = 'Invoice No: A1\nSubtotal: USD 100\nTax: USD 20\nTotal: USD 130'
        page.save()
        data = parse_invoice_pages([page])
        self.assertTrue(data['warnings'])

    def test_list_filter_validation(self):
        self.client.force_authenticate(self.alice)
        self.assertEqual(self.client.get('/api/invoices/?document_id=x').status_code, 400)
