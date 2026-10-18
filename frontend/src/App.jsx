import ClassificationPanel from './ClassificationPanel.jsx';
import { classificationLabel } from './classification.js';
import AsyncJobPanel from './AsyncJobPanel.jsx';
import AnalyticsDashboard from './AnalyticsDashboard.jsx';
import ReviewQueue from './ReviewQueue.jsx';
import EvidenceViewer from './EvidenceViewer.jsx';
import { useCallback, useEffect, useState } from 'react';
import { api, allDocuments, validateUpload, queryString, triggerDownload } from './api.js';

const nav = [ ['documents', 'Documents'], ['invoices', 'Invoice intelligence'], ['reviews', 'Human review'], ['analytics', 'Supplier analytics'], ['ask', 'Ask documents'] ];
const statuses = ['unknown', 'pending', 'paid', 'disputed'];
function Message({ text, kind = 'info', onClose }) {
  if (!text) return null;
  return <div className={`notice ${kind === 'error' ? 'notice-error' : 'notice-info'}`} role={kind === 'error' ? 'alert' : 'status'}><span>{text}</span><button type="button" aria-label="Dismiss message" onClick={onClose}>×</button></div>;
}
function Card({ label, value, detail }) {
  return <div className="metric"><p>{label}</p><strong>{value}</strong>{detail && <small>{detail}</small>}</div>;
}
function authError(error) { return error instanceof Error ? error.message : String(error); }

export default function App() {
  const [credentials, setCredentials] = useState(null);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loginBusy, setLoginBusy] = useState(false);
  const [loginError, setLoginError] = useState('');
  const [tab, setTab] = useState('documents');
  const [documents, setDocuments] = useState([]);
  const [documentsBusy, setDocumentsBusy] = useState(false);
  const [documentError, setDocumentError] = useState('');
  const [title, setTitle] = useState('');
  const [file, setFile] = useState(null);
  const [busyId, setBusyId] = useState(null);
  const [uploadBusy, setUploadBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [pages, setPages] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [summary, setSummary] = useState(null);
  const [invoiceError, setInvoiceError] = useState('');
  const [invoiceBusy, setInvoiceBusy] = useState(false);
  const [lineItemView, setLineItemView] = useState(null);
  const [lineItemBusy, setLineItemBusy] = useState(false);
  const [statusFilter, setStatusFilter] = useState('');
  const [dueFilter, setDueFilter] = useState('');
  const [question, setQuestion] = useState('');
  const [selectedDocs, setSelectedDocs] = useState([]);
  const [answer, setAnswer] = useState(null);
  const [retrievalMode, setRetrievalMode] = useState('keyword');
  const [askError, setAskError] = useState('');
  const [asking, setAsking] = useState(false);
  const [pdfEvidence, setPdfEvidence] = useState(null);
  const [processingJob, setProcessingJob] = useState(null);

  const loadDocs = useCallback(async (auth) => {
    setDocumentsBusy(true); setDocumentError('');
    try { setDocuments(await allDocuments(auth)); }
    catch (error) { setDocumentError(authError(error)); }
    finally { setDocumentsBusy(false); }
  }, []);
  const loadInvoices = useCallback(async (auth, filters = {}) => {
    setInvoiceBusy(true); setInvoiceError('');
    try {
      const qs = queryString(filters);
      const [report, data] = await Promise.all([api(`/invoices/report/${qs ? `?${qs}` : ''}`, auth), api('/invoices/dashboard/', auth)]);
      setInvoices(report.results || []); setSummary(data);
    } catch (error) { setInvoiceError(authError(error)); }
    finally { setInvoiceBusy(false); }
  }, []);

  useEffect(() => { if (credentials) { loadDocs(credentials); loadInvoices(credentials); } }, [credentials, loadDocs, loadInvoices]);

  async function login(event) {
    event.preventDefault(); setLoginBusy(true); setLoginError('');
    const proposed = { username: username.trim(), password };
    try { await api('/documents/', proposed); setCredentials(proposed); setPassword(''); }
    catch (error) { setLoginError(authError(error)); }
    finally { setLoginBusy(false); }
  }
  function logout() {
    setCredentials(null); setTab('documents'); setPassword(''); setUsername(''); setDocuments([]); setInvoices([]); setSummary(null); setLineItemView(null); setAnswer(null); setPages(null); setPdfEvidence(null); setMessage(''); setSelectedDocs([]); setProcessingJob(null);
  }
  async function upload(event) {
    event.preventDefault(); if (!credentials) return;
    const validationError = validateUpload(file);
    if (validationError) { setDocumentError(validationError); return; }
    const form = event.currentTarget; setUploadBusy(true); setDocumentError(''); setMessage('');
    try {
      const data = new FormData(); data.append('file', file); if (title.trim()) data.append('title', title.trim());
      await api('/documents/upload/', credentials, { method: 'POST', body: data });
      setFile(null); setTitle(''); form.reset();
      setMessage('Document uploaded. Select “Extract text” to index its contents.');
      await loadDocs(credentials);
    } catch (error) { setDocumentError(authError(error)); }
    finally { setUploadBusy(false); }
  }
  async function documentAction(document, action) {
    if (action === 'delete' && !window.confirm(`Permanently delete “${document.title}”?`)) return;
    setBusyId(document.id); setDocumentError(''); setMessage('');
    try {
      if (action === 'extract') {
        const data = await api(`/documents/${document.id}/extract/`, credentials, { method: 'POST' });
        setPages(null); setAnswer(null); setPdfEvidence(null); setMessage(`Extracted ${data.page_count} page(s), ${data.character_count} characters.`);
      } else if (action === 'extract-async') {
        const job = await api(`/documents/${document.id}/extract-async/`, credentials, { method: 'POST' });
        setProcessingJob({ ...job, document_title: document.title });
        setMessage('Background extraction queued. The status panel will refresh automatically.');
      } else if (action === 'invoice') {
        await api(`/documents/${document.id}/invoice/extract/`, credentials, { method: 'POST' });
        setMessage('Invoice fields extracted. Review the invoice dashboard before assigning payment status.');
        await loadInvoices(credentials, { payment_status: statusFilter, due: dueFilter });
      } else if (action === 'pages') {
        const result = await api(`/documents/${document.id}/pages/`, credentials);
        setPages({ document, items: result });
      } else {
        await api(`/documents/${document.id}/`, credentials, { method: 'DELETE' });
        setPages(null); setAnswer(null); setPdfEvidence(null); setSelectedDocs(prev => prev.filter(id => id !== document.id));
        setMessage('Document permanently deleted.');
        await loadInvoices(credentials, { payment_status: statusFilter, due: dueFilter });
      }
      await loadDocs(credentials);
    } catch (error) { setDocumentError(authError(error)); }
    finally { setBusyId(null); }
  }
  async function refreshInvoices(event) {
    event?.preventDefault(); await loadInvoices(credentials, { payment_status: statusFilter, due: dueFilter });
  }
  async function changePayment(recordId, nextStatus) {
    setBusyId(`invoice-${recordId}`); setInvoiceError('');
    try {
      await api(`/invoices/${recordId}/payment-status/`, credentials, { method: 'PATCH', body: { payment_status: nextStatus } });
      await loadInvoices(credentials, { payment_status: statusFilter, due: dueFilter });
    } catch (error) { setInvoiceError(authError(error)); }
    finally { setBusyId(null); }
  }
  async function showLineItems(recordId) {
    setInvoiceError('');
    if (lineItemView?.recordId === recordId) { setLineItemView(null); return; }
    setLineItemBusy(true); setLineItemView(null);
    try {
      const data = await api(`/invoices/${recordId}/line-items/`, credentials);
      setLineItemView({ recordId, items: data.results || [] });
    } catch (error) { setInvoiceError(authError(error)); }
    finally { setLineItemBusy(false); }
  }
  async function exportInvoices() {
    setInvoiceError(''); setBusyId('csv');
    try {
      const qs = queryString({ payment_status: statusFilter, due: dueFilter });
      const blob = await api(`/invoices/export/${qs ? `?${qs}` : ''}`, credentials, { download: true });
      triggerDownload(blob, 'docupilot_invoices.csv');
    } catch (error) { setInvoiceError(authError(error)); }
    finally { setBusyId(null); }
  }
  async function submitQuestion(event) {
    event.preventDefault(); setAsking(true); setAskError(''); setAnswer(null);
    try {
      const data = { question: question.trim() };
      if (selectedDocs.length) data.document_ids = selectedDocs;
      setAnswer(await api('/ask/', credentials, { method: 'POST', body: { ...data, mode: retrievalMode } }));
    } catch (error) { setAskError(authError(error)); }
    finally { setAsking(false); }
  }

  if (!credentials) return <main className="login-page"><section className="login-panel"><div className="brand"><span className="brand-icon">D</span><span>DocuPilot <b>AI</b></span></div><span className="eyebrow">INTELLIGENT DOCUMENT WORKSPACE</span><h1>Turn documents into decisions.</h1><p className="muted">Sign in with an existing Django account to manage private documents, extract invoices and ask evidence-grounded questions.</p><form onSubmit={login} className="form-stack"><label>Username<input required autoComplete="username" value={username} onChange={e => setUsername(e.target.value)} /></label><label>Password<input required type="password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} /></label><button className="primary" disabled={loginBusy}>{loginBusy ? 'Signing in…' : 'Sign in'}</button></form><Message text={loginError} kind="error" onClose={() => setLoginError('')} /><div className="security-note">Credentials are kept in memory only, never stored in browser storage. This development login uses HTTP Basic authentication; use HTTPS for any remote deployment.</div></section></main>;

  return <div className="app-shell"><aside className="sidebar"><div className="brand"><span className="brand-icon">D</span><span>DocuPilot <b>AI</b></span></div><p className="sidebar-label">WORKSPACE</p><nav aria-label="Primary navigation">{nav.map(([key,label]) => <button key={key} onClick={() => setTab(key)} className={`nav-item ${tab === key ? 'active' : ''}`}>{label}</button>)}</nav><div className="sidebar-bottom"><span>Signed in as <strong>{credentials.username}</strong></span><button className="ghost" onClick={logout}>Sign out</button></div></aside><main className="main-panel"><header className="topbar"><div><span className="eyebrow">TECH_INNOVATORS / DOCUPILOT AI</span><h1>{nav.find(([key]) => key === tab)?.[1]}</h1></div><span className="environment-tag">SQLite3 · MVP</span></header><div className="main-content">
  {tab === 'documents' && <><div className="intro"><h2>Document library</h2><p>Upload PDF, UTF-8 TXT, PNG or JPEG files (10 MiB maximum). Scanned pages use local OCR. Private documents are accessible only to their owner.</p></div><div className="panel"><h3>Upload document</h3><form onSubmit={upload} className="upload-form"><label>Document title (optional)<input maxLength={255} value={title} onChange={e => setTitle(e.target.value)} placeholder="e.g. Supplier invoice October" /></label><label>Choose PDF, TXT or image<input type="file" accept=".pdf,.txt,.png,.jpg,.jpeg,application/pdf,text/plain,image/png,image/jpeg" required onChange={e => setFile(e.target.files?.[0] || null)} /></label><button className="primary" disabled={uploadBusy || !file}>{uploadBusy ? 'Uploading…' : 'Upload document'}</button></form></div>{processingJob && <AsyncJobPanel job={processingJob} auth={credentials} onClose={() => setProcessingJob(null)} onUpdate={setProcessingJob} onComplete={() => { loadDocs(credentials); setPages(null); setAnswer(null); }} />}
<Message text={documentError} kind="error" onClose={() => setDocumentError('')}/><Message text={message} onClose={() => setMessage('')}/><div className="panel"><div className="panel-heading"><h3>Your documents</h3><button className="secondary" onClick={() => loadDocs(credentials)} disabled={documentsBusy}>Refresh</button></div>{documentsBusy ? <p role="status">Loading documents…</p> : documents.length === 0 ? <div className="empty-state">No documents yet. Upload a PDF, TXT or image file to begin.</div> : <div className="document-list">{documents.map(doc => <article className="document-item" key={doc.id}><div><h4>{doc.title}</h4><p>Classification: {classificationLabel(doc.classification_category)}</p><p>{(doc.file_type || 'file').toUpperCase()} · {doc.processing_status} · {doc.original_filename || 'metadata only'}</p></div><div className="actions"><button disabled={busyId === doc.id || !doc.has_file} onClick={() => documentAction(doc, 'extract')}>Extract text</button><button disabled={busyId === doc.id || !doc.has_file} onClick={() => documentAction(doc, 'extract-async')}>Background extract</button><button disabled={busyId === doc.id} onClick={() => documentAction(doc, 'pages')}>View pages</button><button disabled={busyId === doc.id || doc.processing_status !== 'completed'} onClick={() => documentAction(doc, 'invoice')}>Extract invoice</button><button className="danger" disabled={busyId === doc.id} onClick={() => documentAction(doc, 'delete')}>Delete</button></div><ClassificationPanel document={doc} auth={credentials} onUpdated={() => loadDocs(credentials)} /></article>)}</div>}</div>{pages && <section className="panel"><div className="panel-heading"><h3>Extracted pages · {pages.document.title}</h3><button className="secondary" onClick={() => setPages(null)}>Close</button></div>{pages.items.length === 0 ? <p className="muted">No text extracted yet.</p> : pages.items.map(page => <div className="page-excerpt" key={page.id}><strong>Page {page.page_number}</strong><pre>{page.extracted_text}</pre></div>)}</section>}</>}
  {tab === 'reviews' && <ReviewQueue auth={credentials} />}
  {tab === 'analytics' && <AnalyticsDashboard auth={credentials} />}
  {tab === 'invoices' && <><div className="intro"><h2>Invoice intelligence</h2><p>Due dates and balances are derived from extracted documents. Payment status is manually confirmed by the document owner.</p></div><Message text={invoiceError} kind="error" onClose={() => setInvoiceError('')}/><div className="metrics"><Card label="Extracted invoices" value={summary?.invoice_count ?? '—'} /><Card label="Pending" value={summary?.payment_status_counts?.pending ?? '—'} /><Card label="Overdue pending" value={summary?.overdue_pending_count ?? '—'} /><Card label="Unconfirmed past due" value={summary?.past_due_unconfirmed_count ?? '—'} /></div><div className="panel"><h3>Pending totals by currency</h3><div className="currency-row">{summary && Object.keys(summary.pending_totals_by_currency || {}).length ? Object.entries(summary.pending_totals_by_currency).map(([currency, amount]) => <span className="currency-chip" key={currency}>{currency} <strong>{amount}</strong></span>) : <span className="muted">No confirmed pending balances.</span>}</div><p className="footnote">Missing or invalid amounts are excluded, never treated as zero. {summary?.pending_without_usable_total_count ?? 0} pending invoices excluded.</p></div><div className="panel"><form className="filters" onSubmit={refreshInvoices}><label>Payment status<select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}><option value="">All statuses</option>{statuses.map(s => <option key={s}>{s}</option>)}</select></label><label>Due category<select value={dueFilter} onChange={e => setDueFilter(e.target.value)}><option value="">All due dates</option>{['overdue','due_today','upcoming','undated','past_due_unconfirmed'].map(s => <option key={s} value={s}>{s.replaceAll('_',' ')}</option>)}</select></label><button className="secondary" disabled={invoiceBusy}>Apply filters</button><button type="button" className="primary" disabled={busyId === 'csv'} onClick={exportInvoices}>Export CSV</button></form><div className="panel-heading"><h3>Invoice records</h3><span className="muted">{invoices.length} matching records</span></div>{invoiceBusy ? <p role="status">Loading invoice report…</p> : !invoices.length ? <div className="empty-state">No invoices match these filters. Extract invoice fields from a processed document first.</div> : <div className="table-wrap"><table><thead><tr><th>Invoice</th><th>Supplier</th><th>Due date</th><th>Total</th><th>Due category</th><th>Payment status</th><th>Details</th></tr></thead><tbody>{invoices.map(row => <tr key={row.record_id}><td><strong>{row.invoice_number || 'Unverified'}</strong><small>{row.document_title}</small></td><td>{row.supplier || '—'}</td><td>{row.due_date || '—'}</td><td>{row.total ? `${row.currency || '?'} ${row.total}` : '—'}</td><td>{row.due_category?.replaceAll('_', ' ')}</td><td><select aria-label={`Payment status for invoice ${row.record_id}`} disabled={busyId === `invoice-${row.record_id}`} value={row.payment_status} onChange={e => changePayment(row.record_id, e.target.value)}>{statuses.map(s => <option key={s}>{s}</option>)}</select></td><td><button type="button" className="secondary" disabled={lineItemBusy} onClick={() => showLineItems(row.record_id)}>Line items</button></td></tr>)}</tbody></table></div>}{lineItemBusy && <p role="status">Loading line items…</p>}{lineItemView && <div className="line-items-panel"><div className="panel-heading"><h3>Invoice {lineItemView.recordId} · Line items</h3><button className="secondary" onClick={() => setLineItemView(null)}>Close</button></div>{lineItemView.items.length === 0 ? <p>No confidently recognized line-item rows. Review the original invoice.</p> : <div className="table-wrap"><table><thead><tr><th>Description</th><th>Quantity</th><th>Unit price</th><th>Line total</th><th>Validation</th><th>Source page</th></tr></thead><tbody>{lineItemView.items.map(item => <tr key={item.line_number}><td title={item.source_excerpt}>{item.description}</td><td>{item.quantity}</td><td>{item.unit_price}</td><td>{item.line_total}</td><td>{item.validation_status}</td><td>Page {item.page_number}</td></tr>)}</tbody></table></div>}<p className="footnote">Automatically extracted rows are unreviewed; verify against the original document.</p></div>}</div></>}
  {tab === 'ask' && <><div className="intro"><h2>Ask your documents</h2><p>Find document evidence using keyword, semantic or hybrid retrieval. Answers quote source passages—not generated claims.</p></div><div className="panel"><form onSubmit={submitQuestion} className="form-stack"><label>Your question<textarea maxLength={500} required rows={3} value={question} onChange={e => setQuestion(e.target.value)} placeholder="What does the refund policy say?" /></label><label>Retrieval method<select aria-label="Retrieval method" value={retrievalMode} onChange={e => setRetrievalMode(e.target.value)}><option value="keyword">Keyword (fast, offline)</option><option value="semantic">Semantic (local multilingual model)</option><option value="hybrid">Hybrid (semantic + keyword)</option></select></label><fieldset className="doc-selector"><legend>Search scope</legend><p className="muted">Select documents, or leave all unchecked to search every indexed document you own.</p><div className="selector-options">{documents.length ? documents.map(doc => <label key={doc.id} className="check-row"><input type="checkbox" checked={selectedDocs.includes(doc.id)} onChange={e => setSelectedDocs(prev => e.target.checked ? [...prev, doc.id] : prev.filter(id => id !== doc.id))} />{doc.title}</label>) : <span className="muted">No documents uploaded</span>}</div></fieldset><button className="primary" disabled={asking || !question.trim()}>{asking ? 'Searching evidence…' : 'Ask documents'}</button></form></div><Message text={askError} kind="error" onClose={() => setAskError('')}/>{answer && <section className="panel" aria-live="polite"><h3>{answer.has_evidence ? 'Evidence-based answer' : 'Insufficient evidence'}</h3><p className="answer-text">{answer.answer}</p>{answer.has_evidence && <><h4 className="sources-heading">Supporting sources</h4>{(answer.source_references || []).map((ref,i) => <div className="source" key={`${ref.chunk_id}-${i}`}><strong>{ref.document_title} · Page {ref.page_number}</strong><p>{ref.excerpt}</p><small>Document #{ref.document_id} · Chunk #{ref.chunk_id} · {ref.retrieval_method || "keyword"}</small>{documents.find(d => d.id === ref.document_id)?.file_type?.toLowerCase() === 'pdf' && <button type="button" className="secondary" onClick={() => setPdfEvidence(ref)}>View highlighted PDF · page {ref.page_number}</button>}</div>)}</>}{pdfEvidence && <EvidenceViewer evidence={pdfEvidence} auth={credentials} onClose={() => setPdfEvidence(null)} />}<p className="footnote">Extractive search only. Verify supporting passages against their original documents.</p></section>}</>}
</div></main></div>;
}
