import { useEffect, useState } from 'react';
import { api } from './api.js';
import { summarizeFeedback, validateLabelExport } from './feedbackQuality.js';

export default function FeedbackQuality({ auth }) {
  const [report, setReport] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let active = true;
    api('/classification/feedback-quality/', auth).then(v => { if(active) setReport(v); })
      .catch(e => { if(active) setError(e.message); });
    return () => { active = false; };
  }, [auth]);
  const summary = summarizeFeedback(report);
  async function exportLabels() {
    if (!window.confirm('Export only pseudonymous operational label pairs? This is not independent ground truth.')) return;
    setBusy(true); setError('');
    try {
      const result = await api('/classification/feedback-label-export/', auth,
        { method: 'POST', body: { confirm_label_only_export: true } });
      if (!validateLabelExport(result)) throw new Error('Invalid privacy-safe export response');
      const url = URL.createObjectURL(new Blob([JSON.stringify(result,null,2)], {type:'application/json'}));
      const link = document.createElement('a');
      link.href=url; link.download='docupilot_feedback_labels.json'; link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch(e) { setError(e.message); }
    finally { setBusy(false); }
  }
  return <section className="panel" aria-label="Classification feedback quality">
    <h2>Classification feedback quality</h2>
    <p className="footnote">Owner review agreement is not model accuracy. Reviewed documents are not independently adjudicated ground truth.</p>
    {error && <p role="alert" className="notice notice-error">{error}</p>}
    {!report && !error && <p role="status">Loading feedback quality…</p>}
    {summary && <>
      <p>{summary.reviewed} reviewed · {summary.agreement} agreements · {summary.disagreement} disagreements</p>
      <p>Review coverage: {summary.coverage === null ? 'N/A' : `${(summary.coverage*100).toFixed(1)}%`} · Agreement among reviewed: {summary.rate === null ? 'N/A' : `${(summary.rate*100).toFixed(1)}%`}</p>
      <p>Machine predictions changed since feedback: {report.machine_changed_since_decision_count}</p>
      <div className="table-wrap"><table><caption>Machine label at review (rows) compared with owner label (columns)</caption>
        <thead><tr><th>Machine / Human</th>{report.labels.map(label=><th key={label}>{label}</th>)}</tr></thead>
        <tbody>{report.labels.map(machine=><tr key={machine}><th scope="row">{machine}</th>{report.labels.map(human=><td key={human}>{report.confusion_matrix[machine]?.[human] ?? 0}</td>)}</tr>)}</tbody>
      </table></div>
      <p className="footnote">Exports contain random per-download aliases, classification label pairs and review actions only. No file names, documents, excerpts, reviewer names or notes. No original text is provided for a classifier benchmark.</p>
      <button type="button" className="secondary" disabled={busy} onClick={exportLabels}>{busy?'Preparing…':'Export privacy-safe label pairs'}</button>
    </>}
  </section>;
}
