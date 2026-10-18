import test from 'node:test';
import assert from 'node:assert/strict';
import { validateReliability, triageRows } from './reliability.js';
test('rejects independently-ground-truth wording', () => {
 assert.equal(validateReliability({basis:'independently_adjudicated_documents',reviewed_document_count:1,priority_order:[],triage_counts:{}}),false);
});
test('preserves explicit triage ordering', () => {
 const report={basis:'owner_operational_feedback_not_independent_ground_truth',reviewed_document_count:2,priority_order:['missing_machine_prediction','review_disagreements'],triage_counts:{missing_machine_prediction:0,review_disagreements:2}};
 assert.deepEqual(triageRows(report).map(r=>r.count),[0,2]);
});
