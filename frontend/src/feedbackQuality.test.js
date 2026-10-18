import test from 'node:test';
import assert from 'node:assert/strict';
import { summarizeFeedback, validateLabelExport } from './feedbackQuality.js';

test('quality report does not accept independent accuracy as operational agreement', () => {
  assert.equal(summarizeFeedback({basis: 'independent_accuracy'}), null);
  const result = summarizeFeedback({basis:'operational_owner_feedback_not_independent_ground_truth', reviewed_document_count:2,agreement_count:1,disagreement_count:1,coverage_rate:.5,agreement_rate:.5});
  assert.equal(result.disagreement,1);
  assert.equal(result.coverage,.5);
});

test('export explicitly rejects independently labeled claim', () => {
  const data = {dataset_type:'pseudonymous_operational_feedback_labels_only',independent_ground_truth:false,cases:[{sample_id:'random',machine_label_at_review:'invoice',human_label:'contract'}]};
  assert.equal(validateLabelExport(data),true);
  assert.equal(validateLabelExport({...data,independent_ground_truth:true}),false);
});
