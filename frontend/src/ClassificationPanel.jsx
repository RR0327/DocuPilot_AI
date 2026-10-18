import { useState } from 'react';
import { api } from './api.js';
import { validClassification, classificationLabel } from './classification.js';

export default function ClassificationPanel({ document, auth, onUpdated }) {
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function run(method) {
    setBusy(true); setError('');
    try {
      const data = await api(`/documents/${document.id}/classification/`, auth, { method });
      if (!validClassification(data)) throw new Error('Unexpected classification response');
      setResult(data);
      if (method === 'POST') onUpdated?.();
    } catch (e) { setError(e.message || 'Classification unavailable'); }
    finally { setBusy(false); }
  }
  return <section className="classification-panel">
    <div className="actions"><button type="button" className="secondary" disabled={busy} onClick={() => run('GET')}>View evidence</button>
    <button type="button" className="secondary" disabled={busy || document.processing_status !== 'completed'} onClick={() => run('POST')}>Reclassify</button></div>
    {error && <p role="alert" className="notice notice-error">{error}</p>}
    {result && <div className="classification-detail"><strong>{classificationLabel(result.category)}</strong> <small>{result.reason}</small>
      <p className="footnote">Rule weights are not probability or confidence scores. Validate against the original source. OCR and Bangla signals may be imperfect.</p>
      {result.evidence.length ? <ul>{result.evidence.map((item, i) => <li key={`${item.page_number}-${item.phrase}-${i}`}>Page {item.page_number} · {item.category} · “{item.phrase}” {item.signal && item.signal !== item.phrase ? `(signal: ${item.signal})` : null} — <span>{item.excerpt}</span></li>)}</ul> : <p>No category evidence found.</p>}
    </div>}
  </section>;
}
