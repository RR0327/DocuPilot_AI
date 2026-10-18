import test from 'node:test';
import assert from 'node:assert/strict';
import { validClassification, evaluationSummary } from './classification.js';
test('OCR alias evidence permits an auditable source phrase', () => {
  assert.equal(validClassification({category:'invoice', reason:'Rule evidence', evidence:[{page_number:1,phrase:'Inv0ice No', signal:'invoice no',excerpt:'Inv0ice No: 12'}]}), true);
});
test('evaluation remains synthetic and cannot masquerade as independent benchmark', () => {
  assert.equal(evaluationSummary({dataset_type:'externally_labeled_user_dataset',sample_count:10,macro_f1:1,labels:['invoice'],confusion_matrix:{}}),null);
});
