import { useState } from 'react';
import { api } from './api.js';
import { CATEGORIES, classificationLabel } from './classification.js';

export default function ClassificationReview({ document, auth }) {
  const [data, setData] = useState(null);
  const [category, setCategory] = useState('unknown');
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function load() {
    setBusy(true); setError('');
    try {
      const next = await api(`/documents/${document.id}/classification-review/`, auth);
      setData(next); setCategory(next.effective_category || 'unknown');
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }
  async function decide(action) {
    setBusy(true); setError('');
    try {
      const next = await api(`/documents/${document.id}/classification-review/`, auth,
        { method: 'POST', body: { action, category: action === 'clear' ? '' : action === 'verify' ? data.machine_category : category, note } });
      setData(next); setCategory(next.effective_category || 'unknown'); setNote('');
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }
  return <section className="classification-panel" aria-label="Classification human review">
    <button type="button" className="secondary" disabled={busy} onClick={load}>Review category / history</button>
    {error && <p role="alert" className="notice notice-error">{error}</p>}
    {data && <div className="classification-detail">
      <p>Machine prediction: <strong>{classificationLabel(data.machine_category)}</strong></p>
      <p>Effective category: <strong>{classificationLabel(data.effective_category)}</strong> · {data.review_status}</p>
      <p className="footnote">Human labels are separate from machine predictions and do not establish independent classification accuracy.</p>
      <label>Reviewed category <select value={category} disabled={busy} onChange={e => setCategory(e.target.value)}>{CATEGORIES.map(item => <option value={item} key={item}>{classificationLabel(item)}</option>)}</select></label>
      <label>Review reason <textarea rows={2} maxLength={1000} value={note} onChange={e => setNote(e.target.value)} /></label>
      <div className="actions">
        <button type="button" className="secondary" disabled={busy || !data.machine_category} onClick={() => decide('verify')}>Verify prediction</button>
        <button type="button" className="secondary" disabled={busy || category === data.machine_category || !note.trim()} onClick={() => decide('override')}>Save override</button>
        <button type="button" className="secondary" disabled={busy} onClick={() => decide('clear')}>Clear review</button>
      </div>
      <h5>Review history ({data.history.length})</h5>
      {data.history.length ? <ul>{data.history.map(item => <li key={item.id}>{item.action}: {classificationLabel(item.category)} · {new Date(item.created_at).toLocaleString()} · {item.note || 'No note'}</li>)}</ul> : <p>No human reviews yet.</p>}
      <h5>Original machine evidence</h5>
      <ul>{data.source_evidence.map((item, i) => <li key={i}>Page {item.page_number}: {item.excerpt}</li>)}</ul>
    </div>}
  </section>;
}
