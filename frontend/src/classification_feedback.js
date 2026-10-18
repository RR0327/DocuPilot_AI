export function validFeedback(data) {
  return !!data && Number.isInteger(data.document_id) &&
    Array.isArray(data.history) && Array.isArray(data.source_evidence) &&
    typeof data.review_status === 'string';
}
export function feedbackStats(result) {
  if (!result || result.basis !== 'owner_review_feedback_not_independent_accuracy') return null;
  return result.counts;
}
