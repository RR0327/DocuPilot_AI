import { useEffect, useState } from 'react';
import { api } from './api.js';

const keys = ['invoice_number','supplier','invoice_date','due_date','subtotal','tax','total','currency'];
export default function ReviewQueue({ auth }) {
  const [status, setStatus] = useState('unreviewed');
  const [items, setItems] = useState([]);
  const [active, setActive] = useState(null);
  const [changes, setChanges] = useState({});
  const [note, setNote] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(false);
  async function refresh() {
    setLoading(true); setError('');
    try { const result = await api(`/reviews/?status=${status}`, auth); setItems(result.results || []); }
    catch (err) { setError(err.message); }
    finally { setLoading(false); }
  }
  useEffect(() => { refresh(); }, [auth, status]);
  async function openRecord(id) {
    setBusy(true); setError('');
    try { setActive(await api(`/reviews/${id}/`, auth)); setChanges({}); setNote(''); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }
  async function submit(action) {
    if (!active) return;
    setBusy(true); setError('');
    try {
      const body = { action, note };
      if (action === 'approve' && Object.keys(changes).length) body.corrections = changes;
      const updated = await api(`/reviews/${active.record_id}/`, auth, { method: 'POST', body });
      setActive(updated); setChanges({}); setNote(''); await refresh();
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }
  return <section className="panel" aria-label="Human review queue">
    <div className="panel-heading"><h2>Human review queue</h2><button className="secondary" onClick={refresh} disabled={loading}>Refresh</button></div>
    <p className="muted">Review extracted invoice data against source evidence. Approval records corrections separately; original extraction and citations remain unchanged.</p>
    <label>Review status <select aria-label="Review status" value={status} onChange={e => setStatus(e.target.value)}><option value="unreviewed">Unreviewed</option><option value="valid">Approved</option><option value="invalid">Rejected</option><option value="all">All</option></select></label>
    {error && <p role="alert" className="notice notice-error">{error}</p>}
    {loading ? <p role="status">Loading reviews…</p> : !items.length ? <p>No matching invoice extractions.</p> : <div className="document-list">{items.map(item => <article className="document-item" key={item.record_id}><div><strong>{item.document_title}</strong><p>Record #{item.record_id} · {item.validation_status}{item.needs_attention ? ' · Needs attention' : ''}</p><small>{item.quality_flags.join('; ') || 'No extraction warnings recorded'}</small></div><button className="secondary" onClick={() => openRecord(item.record_id)}>Review</button></article>)}</div>}
    {active && <section className="line-items-panel" aria-label="Review details"><div className="panel-heading"><h3>Review invoice #{active.record_id}</h3><button className="secondary" onClick={() => setActive(null)}>Close</button></div>
      <p>Status: <strong>{active.validation_status}</strong></p>
      {active.quality_flags.length > 0 && <p className="footnote">Quality warnings: {active.quality_flags.join('; ')}</p>}
      <div className="review-fields">{keys.map(key => <label key={key}>{key.replaceAll('_',' ')}
        <input disabled={active.validation_status !== 'unreviewed'} aria-label={`Correct ${key}`} value={Object.hasOwn(changes,key) ? changes[key] : (active.effective_fields[key] ?? '')} onChange={e => setChanges(prev => ({...prev,[key]:e.target.value}))} />
        {active.source_references[key] && <small>Source page {active.source_references[key].page_number}: {active.source_references[key].excerpt}</small>}
      </label>)}</div>
      <label>Review note<textarea rows={2} aria-label="Review note" value={note} onChange={e => setNote(e.target.value)} /></label>
      <div className="actions">{active.validation_status === 'unreviewed' ? <><button disabled={busy} className="primary" onClick={() => submit('approve')}>Approve with corrections</button><button disabled={busy} className="danger" onClick={() => submit('reject')}>Reject (reason required)</button></> : <button disabled={busy} className="secondary" onClick={() => submit('reopen')}>Reopen for review</button>}</div>
      <h4>Review history</h4>{active.history.length === 0 ? <p>No decisions recorded.</p> : <div>{active.history.map(h => <p key={h.id}><strong>{h.action}</strong> · {h.reviewed_at} · {h.note || 'No note'} · {Object.keys(h.corrections).length} corrections</p>)}</div>}
    </section>}
  </section>;
}
