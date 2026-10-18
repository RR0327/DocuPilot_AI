"""Phase 4 Step 3 multilingual, OCR and independent dataset safeguards."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from django.test import SimpleTestCase
from .classification import classify_pages
from .classification_evaluation import evaluate_cases, evidence_issues, run_external_dataset


class RefinementTests(SimpleTestCase):
    def test_bangla_categories_and_original_evidence(self):
        samples = {'invoice': 'চালান নম্বর ১০২, বিলের তারিখ আজ।',
                   'policy': 'গোপনীয়তা নীতি এবং ফেরত নীতি।',
                   'report': 'নির্বাহী সারসংক্ষেপ। গবেষণা পদ্ধতি।',
                   'contract': 'এই চুক্তি কার্যকর। চুক্তির শর্ত এখানে।'}
        for expected, text in samples.items():
            with self.subTest(expected=expected):
                label, evidence, _, _ = classify_pages([(2, text)])
                self.assertEqual(label, expected)
                self.assertFalse(evidence_issues([(2, text)], evidence))
                self.assertTrue(all(e['page_number'] == 2 for e in evidence))

    def test_ocr_alias_and_line_break_match(self):
        text = 'Inv0ice No: 42\nInvoice\nDate 2026-10-18. Subtotal 20.'
        label, evidence, _, _ = classify_pages([(1, text)])
        self.assertEqual(label, 'invoice')
        self.assertFalse(evidence_issues([(1, text)], evidence))

    def test_unknown_and_mixed_evidence(self):
        self.assertEqual(classify_pages([(1, 'Personal journal entry.')])[0], 'unknown')
        self.assertEqual(classify_pages([(1, 'Invoice No: 1 Privacy Policy')])[0], 'unknown')

    def test_error_analysis_separates_unsafe_guesses(self):
        report = evaluate_cases([{'id':'x','label':'unknown','pages':[{'page_number':1,'text':'Invoice No: 44'}]},
                                 {'id':'y','label':'policy','pages':[{'page_number':1,'text':'Personal journal.'}]}])
        self.assertEqual(report['error_analysis']['unsafe_guess'],1)
        self.assertEqual(report['error_analysis']['false_abstention'],1)

    def test_external_dataset_requires_provenance(self):
        with TemporaryDirectory() as tmp:
            file = Path(tmp)/'labels.json'
            file.write_text(json.dumps({'cases':[{'id':'x','label':'unknown','pages':[{'page_number':1,'text':'Hello'}]}]}))
            with self.assertRaises(ValueError): run_external_dataset(file)
            provenance={'labeling_method':'independent_human_review', 'reviewer_protocol':'two annotators, blind review and adjudication', 'source_description':'consented internal testing data'}
            file.write_text(json.dumps({'provenance':provenance,'cases':[{'id':'x','label':'unknown','pages':[{'page_number':1,'text':'Hello'}]}]}))
            report=run_external_dataset(file)
            self.assertEqual(report['dataset_type'],'externally_labeled_user_dataset')
            self.assertEqual(report['provenance'],provenance)
