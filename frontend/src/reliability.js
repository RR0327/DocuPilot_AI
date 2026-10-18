export function validateReliability(report) {
  return !!report && report.basis === 'owner_operational_feedback_not_independent_ground_truth' &&
    Number.isInteger(report.reviewed_document_count) && report.reviewed_document_count >= 0 &&
    Array.isArray(report.priority_order) && !!report.triage_counts &&
    report.priority_order.every(key => Number.isInteger(report.triage_counts[key]) && report.triage_counts[key]>=0);
}
export function triageRows(report) {
  if (!validateReliability(report)) return [];
  return report.priority_order.map(key => ({ key, count: report.triage_counts[key] }));
}
