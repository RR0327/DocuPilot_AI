import test from 'node:test';
import assert from 'node:assert/strict';
import { evaluationSummary } from './classification.js';
test('class quality validates published schema and labels fixture honestly', () => {
  assert.deepEqual(evaluationSummary({dataset_type:'synthetic_regression_fixture', sample_count:15, macro_f1:0.8, labels:['unknown'], confusion_matrix:{}, evidence_issue_count:0}), {count:15, f1:0.8, integrity:'No fixture issues'});
  assert.equal(evaluationSummary({dataset_type:'production',sample_count:15,macro_f1:0.8,labels:[],confusion_matrix:{}}), null);
});
test('missing numerical data is not reported as a valid quality score', () => {
  assert.equal(evaluationSummary({dataset_type:'synthetic_regression_fixture',sample_count:15,macro_f1:NaN,labels:[],confusion_matrix:{}}),null);
});
