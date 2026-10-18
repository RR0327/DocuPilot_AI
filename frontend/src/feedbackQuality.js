export function summarizeFeedback(report) {
  if (!report || report.basis !== 'operational_owner_feedback_not_independent_ground_truth') return null;
  return {
    reviewed: Number(report.reviewed_document_count) || 0,
    agreement: Number(report.agreement_count) || 0,
    disagreement: Number(report.disagreement_count) || 0,
    coverage: report.coverage_rate === null ? null : Number(report.coverage_rate),
    rate: report.agreement_rate === null ? null : Number(report.agreement_rate),
  };
}

export function validateLabelExport(payload) {
  return !!payload && payload.dataset_type === 'pseudonymous_operational_feedback_labels_only' &&
    payload.independent_ground_truth === false && Array.isArray(payload.cases) &&
    payload.cases.every(row => row.sample_id && row.machine_label_at_review && row.human_label);
}
