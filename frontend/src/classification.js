export const CATEGORIES = ['invoice', 'policy', 'report', 'contract', 'unknown'];
export function validClassification(data) {
  return Boolean(data && CATEGORIES.includes(data.category) &&
    Array.isArray(data.evidence) && typeof data.reason === 'string' &&
    data.evidence.every(e => Number.isInteger(e.page_number) && e.page_number > 0 &&
      typeof e.phrase === 'string' && typeof e.excerpt === 'string'));
}
export function classificationLabel(category) {
  return CATEGORIES.includes(category) ? (category === 'unknown' ? 'Needs review' : category[0].toUpperCase() + category.slice(1)) : 'Not classified';
}

export function evaluationSummary(report) {
  if (!report || report.dataset_type !== 'synthetic_regression_fixture' ||
      !Number.isInteger(report.sample_count) || !Number.isFinite(report.macro_f1) ||
      !Array.isArray(report.labels) || !report.confusion_matrix) return null;
  return { count: report.sample_count, f1: report.macro_f1,
    integrity: report.evidence_issue_count === 0 ? 'No fixture issues' : `${report.evidence_issue_count} fixture issues` };
}
