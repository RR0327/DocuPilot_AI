import copy
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient
from .classification_evaluation import evaluate_cases, evidence_issues, run_fixture


class EvaluationMetricTests(SimpleTestCase):
    def test_fixture_has_all_five_categories_and_grounded_evidence(self):
        report = run_fixture()
        self.assertEqual(report['sample_count'], 15)
        self.assertEqual(set(report['labels']), {'invoice','policy','report','contract','unknown'})
        self.assertEqual(report['evidence_issue_count'], 0)
        self.assertEqual(sum(sum(row.values()) for row in report['confusion_matrix'].values()), 15)

    def test_confusion_precision_recall_f1_and_abstentions(self):
        cases = [{'id':'a','label':'invoice','pages':[{'page_number':1,'text':'Invoice No and Invoice Date'}]},
                 {'id':'b','label':'policy','pages':[{'page_number':1,'text':'random content'}]},
                 {'id':'c','label':'unknown','pages':[{'page_number':1,'text':'random content'}]}]
        r = evaluate_cases(cases)
        self.assertEqual(r['confusion_matrix']['policy']['unknown'], 1)
        self.assertEqual(r['per_category']['unknown']['precision'], .5)
        self.assertEqual(r['per_category']['unknown']['recall'], 1.0)
        self.assertEqual(r['per_category']['unknown']['f1'], .6667)

    def test_evidence_integrity_detects_fabricated_page_or_excerpt(self):
        source = [(1, 'The Privacy Policy applies.')]
        evidence = [{'page_number':1,'phrase':'privacy policy','excerpt':'the privacy policy applies.'}]
        self.assertFalse(evidence_issues(source,evidence))
        self.assertTrue(evidence_issues(source,[{**evidence[0], 'page_number':2}]))
        self.assertTrue(evidence_issues(source,[{**evidence[0], 'excerpt':'not from source'}]))

    def test_unknown_reference_class_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_cases([{'id':'bad','label':'other','pages':[]}])


class EvaluationAPITests(TestCase):
    def test_requires_authentication_and_returns_synthetic_report(self):
        client = APIClient()
        path = '/api/classification/evaluation/'
        self.assertIn(client.get(path).status_code, (401,403))
        user = get_user_model().objects.create_user('evaluation_user', password='password')
        client.force_authenticate(user=user)
        response = client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['dataset_type'], 'synthetic_regression_fixture')
        self.assertEqual(response['Cache-Control'],'no-store')
