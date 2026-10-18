import unittest
from .evaluation_metrics import (edit_distance, character_error_rate,
                                 retrieval_metrics, invoice_field_accuracy,
                                 check_source_excerpt)


class EvaluationMetricsTests(unittest.TestCase):
    def test_edit_distance(self):
        self.assertEqual(edit_distance('kitten', 'sitting'), 3)
        self.assertEqual(edit_distance('', ''), 0)

    def test_ocr_errors_and_bangla(self):
        self.assertEqual(character_error_rate('বাংলা', 'বাংলা'), 0.0)
        self.assertAlmostEqual(character_error_rate('abc', 'axc'), 1/3, places=5)
        self.assertEqual(character_error_rate('', 'a'), 1.0)

    def test_retrieval_metrics_and_abstention(self):
        result = retrieval_metrics([{'expected':'a', 'ranked':['b','a'], 'source_integrity':1},
                                    {'expected':None, 'ranked':[], 'source_integrity':1}])
        self.assertEqual(result['recall_at_5'], 1)
        self.assertEqual(result['mrr'], 0.5)
        self.assertEqual(result['no_evidence_abstention_rate'], 1)
        self.assertEqual(result['citation_integrity_rate'], 1)

    def test_empty_denominators_and_invoice(self):
        self.assertIsNone(retrieval_metrics([])['recall_at_5'])
        self.assertEqual(invoice_field_accuracy([({'a':None,'b':'x'}, {'a':None,'b':'y'})])['exact_match_rate'],0.5)

    def test_exact_page_provenance(self):
        self.assertTrue(check_source_excerpt('A refund is allowed.', 'refund is allowed'))
        self.assertFalse(check_source_excerpt('A refund is allowed.', 'unrelated text'))
