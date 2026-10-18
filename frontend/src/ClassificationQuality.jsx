import { useEffect, useState } from 'react';
import { api } from './api.js';
import { evaluationSummary } from './classification.js';

export default function ClassificationQuality({ auth }) {
  const [report, setReport] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    api('/classification/evaluation/', auth).then(data => { if (active) setReport(data); })
      .catch(e => { if (active) setError(e.message || 'Evaluation unavailable'); });
    return () => { active = false; };
  }, [auth]);
  const summary = evaluationSummary(report);
  return <section className="panel classification-quality">
    <h2>Classification quality — synthetic benchmark</h2>
    <p className="footnote">Labeled examples are bundled synthetic regression fixtures. These scores do not measure real-world accuracy.</p>
    {error && <p role="alert">{error}</p>}
    {!summary && !error && <p role="status">Loading evaluation…</p>}
    {summary && <>
      <p>{summary.count} labeled examples · Macro F1: {summary.f1.toFixed(4)} · {summary.integrity}</p>
      <div className="table-wrap"><table><caption>Per-category metrics</caption><thead><tr><th>Category</th><th>Support</th><th>Precision</th><th>Recall</th><th>F1</th></tr></thead><tbody>
        {report.labels.map(label => <tr key={label}><td>{label}</td><td>{report.per_category[label].support}</td><td>{report.per_category[label].precision}</td><td>{report.per_category[label].recall}</td><td>{report.per_category[label].f1}</td></tr>)}
      </tbody></table></div>
      <div className="table-wrap"><table><caption>Confusion matrix — rows are true labels, columns are predictions</caption><thead><tr><th>Actual / Predicted</th>{report.labels.map(label=><th key={label}>{label}</th>)}</tr></thead><tbody>
        {report.labels.map(actual=><tr key={actual}><th scope="row">{actual}</th>{report.labels.map(predicted=><td key={predicted}>{report.confusion_matrix[actual][predicted]}</td>)}</tr>)}
      </tbody></table></div>
      <h3>Error analysis</h3>
      <p>False abstentions: {report.error_analysis?.false_abstention ?? 0} · Unsafe guesses on unknown cases: {report.error_analysis?.unsafe_guess ?? 0} · Wrong category: {report.error_analysis?.wrong_category ?? 0}</p>
      <p className="footnote">To measure independent real-world performance, run the management command with --dataset using a provenance-documented, human-labeled JSON dataset. This page remains synthetic only.</p>
      <p className="footnote">Unknown is a real evaluation label. A tie or weak signal should abstain rather than guess.</p>
    </>}
  </section>;
}
