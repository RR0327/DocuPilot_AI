import test from 'node:test';
import assert from 'node:assert/strict';
import { validFeedback, feedbackStats } from './classification_feedback.js';
test('human classification review shape', () => {
  assert.equal(validFeedback({document_id:1,history:[],source_evidence:[],review_status:'unreviewed'}),true);
  assert.equal(validFeedback({history:[]}),false);
});
test('feedback counts are not classification accuracy', () => {
  assert.deepEqual(feedbackStats({basis:'owner_review_feedback_not_independent_accuracy',counts:{verified:2}}),{verified:2});
  assert.equal(feedbackStats({basis:'synthetic_regression_fixture'}),null);
});
