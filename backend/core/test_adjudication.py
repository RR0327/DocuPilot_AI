"""Adjudication validation and production classifier regression."""
from django.test import SimpleTestCase
from core.adjudication import evaluate_adjudicated

P = {'source_description':'consented documents','license_or_consent':'explicit consent',
     'reviewer_protocol':'blind independent review','adjudicator_protocol':'third reviewer resolves',
     'collection_date':'2026-10-18'}
def dataset(a='invoice',b='invoice',final='invoice',reason=''):
    return {'dataset_type':'independently_adjudicated_documents','provenance':dict(P),
     'cases':[{'id':'x1','reviewer_a':a,'reviewer_b':b,'adjudicated_label':final,'adjudication_reason':reason,
               'pages':[{'page_number':1,'text':'Invoice No: 123 Invoice Date: 2026-10-18 Subtotal 100'}]}]}

class AdjudicationTests(SimpleTestCase):
    def test_valid_agreement_and_no_identifiers_in_report(self):
        result=evaluate_adjudicated(dataset())
        self.assertEqual(result['accuracy'],1)
        self.assertEqual(result['adjudication']['independent_reviewer_agreement_rate'],1)
        self.assertNotIn('cases',result)
    def test_disagreement_requires_reason(self):
        with self.assertRaises(ValueError): evaluate_adjudicated(dataset(b='report'))
        value=evaluate_adjudicated(dataset(b='report',reason='An independent adjudicator read original pages'))
        self.assertEqual(value['adjudication']['independent_reviewer_disagreement_count'],1)
    def test_missing_provenance_fails(self):
        data=dataset();del data['provenance']['license_or_consent']
        with self.assertRaises(ValueError): evaluate_adjudicated(data)
    def test_duplicate_cases_fail(self):
        data=dataset();data['cases'].append(dict(data['cases'][0]))
        with self.assertRaises(ValueError): evaluate_adjudicated(data)
    def test_unknown_reference_is_valid(self):
        result=evaluate_adjudicated(dataset('unknown','unknown','unknown'))
        self.assertEqual(result['sample_count'],1)
        self.assertEqual(result['error_analysis'].get('unsafe_guess'),1)
