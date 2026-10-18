import { signIn, signOut, currentSession, register } from './api.js';
import ReliabilityDashboard from './ReliabilityDashboard.jsx';
import ClassificationReview from './ClassificationReview.jsx';
import ClassificationPanel from './ClassificationPanel.jsx';
import ClassificationQuality from './ClassificationQuality.jsx';
import FeedbackQuality from './FeedbackQuality.jsx';
import { classificationLabel } from './classification.js';
import AsyncJobPanel from './AsyncJobPanel.jsx';
import AnalyticsDashboard from './AnalyticsDashboard.jsx';
import ReviewQueue from './ReviewQueue.jsx';
import EvidenceViewer from './EvidenceViewer.jsx';
import { useCallback, useEffect, useState } from 'react';
import { api, allDocuments, validateUpload, queryString, triggerDownload } from './api.js';

const nav = [ ['documents', 'Documents'], ['invoices', 'Invoice intelligence'], ['reviews', 'Human review'], ['analytics', 'Supplier analytics'], ['classification-quality', 'Classification quality'], ['feedback-quality', 'Feedback quality'], ['reliability', 'Reliability'], ['ask', 'Ask documents'] ];
const statuses = ['unknown', 'pending', 'paid', 'disputed'];
function Message({ text, kind = 'info', onClose }) {
  if (!text) return null;
  return <div className={`notice ${kind === 'error' ? 'notice-error' : 'notice-info'}`} role={kind === 'error' ? 'alert' : 'status'}><span>{text}</span><button type="button" aria-label="Dismiss message" onClick={onClose}>×</button></div>;
}
function Card({ label, value, detail }) {
  return <div className="metric"><p>{label}</p><strong>{value}</strong>{detail && <small>{detail}</small>}</div>;
}
function authError(error) { return error instanceof Error ? error.message : String(error); }

function getInitialPage() {
  if (typeof window === 'undefined') return 'home';
  const path = window.location.pathname.toLowerCase();
  const hash = window.location.hash.toLowerCase();
  if (path === '/login' || hash === '#/login' || hash === '#login') return 'login';
  if (path === '/register' || hash === '#/register' || hash === '#register') return 'register';
  return 'home';
}

export default function App() {
  const [credentials, setCredentials] = useState(null);
  const [publicPage, setPublicPage] = useState(getInitialPage);
  const [previewTab, setPreviewTab] = useState('invoice');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loginBusy, setLoginBusy] = useState(false);
  const [loginError, setLoginError] = useState('');
  const [regUsername, setRegUsername] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regConfirm, setRegConfirm] = useState('');
  const [regBusy, setRegBusy] = useState(false);
  const [regError, setRegError] = useState('');
  const [regSuccess, setRegSuccess] = useState('');
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
  useEffect(() => { let active = true; currentSession().then(session => { if (active && session.authenticated) setCredentials({username: session.username, mode: 'session'}); }).catch(() => {}); return () => {active=false;}; }, []);

  const navigate = useCallback((page) => {
    setPublicPage(page);
    const path = page === 'home' ? '/' : `/${page}`;
    if (typeof window !== 'undefined' && window.location.pathname !== path) {
      window.history.pushState({ page }, '', path);
    }
  }, []);

  useEffect(() => {
    const handlePopState = () => {
      setPublicPage(getInitialPage());
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  async function handleRegister(event) {
    event.preventDefault();
    setRegError('');
    setRegSuccess('');
    if (regPassword !== regConfirm) {
      setRegError('Passwords do not match.');
      return;
    }
    if (regPassword.length < 12) {
      setRegError('Password must be at least 12 characters.');
      return;
    }
    setRegBusy(true);
    try {
      const data = await register(regUsername.trim(), regPassword);
      setRegSuccess(data.detail || 'Account registered successfully! Please sign in.');
      setUsername(regUsername.trim());
      setRegPassword('');
      setRegConfirm('');
      setTimeout(() => {
        navigate('login');
      }, 900);
    } catch (error) {
      setRegError(authError(error));
    } finally {
      setRegBusy(false);
    }
  }

  async function login(event) {
    event.preventDefault(); setLoginBusy(true); setLoginError('');
    try {
      const session = await signIn(username.trim(), password);
      setCredentials({username: session.username, mode: 'session'});
      setPassword('');
      setRegSuccess('');
    } catch (error) { setLoginError(authError(error)); }
    finally { setLoginBusy(false); }
  }
  async function logout() {
    try { await signOut(); } catch (error) { setLoginError(authError(error)); }
    setCredentials(null);
    navigate('home');
    setTab('documents');
    setPassword('');
    setUsername('');
    setRegSuccess('');
    setRegError('');
    setDocuments([]);
    setInvoices([]);
    setSummary(null);
    setLineItemView(null);
    setAnswer(null);
    setPages(null);
    setPdfEvidence(null);
    setMessage('');
    setSelectedDocs([]);
    setProcessingJob(null);
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

  if (!credentials) {
    if (publicPage === 'register') {
      return (
        <div className="dedicated-auth-page">
          <header className="dedicated-auth-header">
            <div className="brand" role="button" tabIndex={0} onClick={() => navigate('home')} style={{ cursor: 'pointer' }}>
              <span className="brand-icon">D</span>
              <span>DocuPilot <b>AI</b></span>
            </div>
            <button className="secondary" type="button" onClick={() => navigate('home')}>← Back to Home</button>
          </header>
          <main className="dedicated-auth-body">
            <div className="auth-card-wide">
              <div className="brand"><span className="brand-icon">D</span><span>DocuPilot <b>AI</b></span></div>
              <span className="eyebrow" style={{ marginTop: '20px', display: 'block' }}>USER REGISTRATION</span>
              <h2>Create your workspace account</h2>
              <p className="desc">Set up an owner-isolated account on this local instance. All documents, extracted invoices, and reviews will remain strictly private to you.</p>
              <form onSubmit={handleRegister} className="form-stack">
                <label>Username
                  <input required autoComplete="username" maxLength={150} value={regUsername} onChange={e => setRegUsername(e.target.value)} placeholder="e.g. charlie" />
                </label>
                <label>Password
                  <input required type="password" autoComplete="new-password" value={regPassword} onChange={e => setRegPassword(e.target.value)} placeholder="Minimum 12 characters" />
                  <span className="form-helper">Must be at least 12 characters long.</span>
                </label>
                <label>Confirm Password
                  <input required type="password" autoComplete="new-password" value={regConfirm} onChange={e => setRegConfirm(e.target.value)} placeholder="Repeat password" />
                </label>
                <button className="primary" disabled={regBusy}>{regBusy ? 'Registering…' : 'Register & Create Account'}</button>
              </form>
              <Message text={regError} kind="error" onClose={() => setRegError('')} />
              <Message text={regSuccess} kind="info" onClose={() => setRegSuccess('')} />
              <div className="auth-switch-row">
                <span>Already registered? <button type="button" onClick={() => { navigate('login'); setUsername(regUsername); }}>Sign in here →</button></span>
                <button type="button" onClick={() => navigate('home')}>Return to Home</button>
              </div>
            </div>
          </main>
        </div>
      );
    }

    if (publicPage === 'login') {
      return (
        <div className="dedicated-auth-page">
          <header className="dedicated-auth-header">
            <div className="brand" role="button" tabIndex={0} onClick={() => navigate('home')} style={{ cursor: 'pointer' }}>
              <span className="brand-icon">D</span>
              <span>DocuPilot <b>AI</b></span>
            </div>
            <button className="secondary" type="button" onClick={() => navigate('home')}>← Back to Home</button>
          </header>
          <main className="dedicated-auth-body">
            <div className="auth-card-wide">
              <div className="brand"><span className="brand-icon">D</span><span>DocuPilot <b>AI</b></span></div>
              <span className="eyebrow" style={{ marginTop: '20px', display: 'block' }}>WORKSPACE SIGN IN</span>
              <h2>Sign in to DocuPilot AI</h2>
              <p className="desc">Enter your credentials to access your private documents, invoices, and evidence-grounded search.</p>
              <Message text={regSuccess} kind="info" onClose={() => setRegSuccess('')} />
              <form onSubmit={login} className="form-stack">
                <label>Username
                  <input required autoComplete="username" value={username} onChange={e => setUsername(e.target.value)} />
                </label>
                <label>Password
                  <input required type="password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} />
                </label>
                <button className="primary" disabled={loginBusy}>{loginBusy ? 'Signing in…' : 'Sign in'}</button>
              </form>
              <Message text={loginError} kind="error" onClose={() => setLoginError('')} />
              <div style={{ marginTop: '16px', fontSize: '12px', color: '#8fa5be' }}>
                Demo accounts: <strong>alice</strong> or <strong>bob</strong> · Password: <code>DemoPass2026!Secure</code>
              </div>
              <div className="auth-switch-row">
                <span>Need an account? <button type="button" onClick={() => navigate('register')}>Register now →</button></span>
                <button type="button" onClick={() => navigate('home')}>Return to Home</button>
              </div>
              <div className="security-note">
                Credentials are kept in memory only; authentication uses a CSRF-protected HttpOnly session cookie.
              </div>
            </div>
          </main>
        </div>
      );
    }

    // Default: Perfect, Full-Featured Home Page
    return (
      <div className="home-view">
        <header className="site-header">
          <div className="brand" role="button" tabIndex={0} onClick={() => navigate('home')} style={{ cursor: 'pointer' }}>
            <span className="brand-icon">D</span>
            <span>DocuPilot <b>AI</b></span>
          </div>
          <nav className="site-header-nav" aria-label="Main Navigation">
            <a href="#capabilities">Capabilities</a>
            <a href="#workflow">Workflow</a>
            <a href="#security">Security</a>
            <a href="#faq">FAQ</a>
            <button type="button" className="btn-login" onClick={() => navigate('login')}>Login</button>
            <button type="button" className="btn-register" onClick={() => navigate('register')}>Get Started</button>
          </nav>
        </header>

        <main className="home-content">
          <section className="hero-center">
            <div className="hero-pill">
              <span className="hero-pill-dot" />
              <span>Tech_Innovators · Private On-Premises Document Intelligence</span>
            </div>
            <h1>Turn Unstructured Documents Into Instant, Auditable Decisions.</h1>
            <p className="hero-subtitle">
              A private, enterprise-grade document intelligence workspace. Extract text with local OCR, parse multi-currency invoice line items, and run hybrid semantic Q&A with exact source passage citations. Zero cloud data leaks.
            </p>
            <div className="hero-cta-group">
              <button type="button" className="btn-hero-primary" onClick={() => navigate('register')}>
                🚀 Create Free Account
              </button>
              <button type="button" className="btn-hero-secondary" onClick={() => navigate('login')}>
                🔐 Access Workspace (Sign In)
              </button>
            </div>

            <div className="hero-stats">
              <div className="stat-box">
                <strong>100%</strong>
                <span>Local Data Sovereignty</span>
              </div>
              <div className="stat-box">
                <strong>0 B</strong>
                <span>Cloud Data Leakage</span>
              </div>
              <div className="stat-box">
                <strong>Multi-Page</strong>
                <span>Tesseract OCR & Layout</span>
              </div>
              <div className="stat-box">
                <strong>&lt; 1s</strong>
                <span>Extractive Q&A Search</span>
              </div>
            </div>
          </section>

          {/* Interactive Technology Inspector Mockup */}
          <section className="preview-showcase">
            <div className="preview-header">
              <div className="window-dots">
                <span className="dot red" />
                <span className="dot yellow" />
                <span className="dot green" />
              </div>
              <div className="preview-tabs">
                <button type="button" className={`preview-tab ${previewTab === 'invoice' ? 'active' : ''}`} onClick={() => setPreviewTab('invoice')}>
                  🧾 Invoice Extraction Preview
                </button>
                <button type="button" className={`preview-tab ${previewTab === 'qa' ? 'active' : ''}`} onClick={() => setPreviewTab('qa')}>
                  🔍 Grounded Evidence Q&amp;A
                </button>
                <button type="button" className={`preview-tab ${previewTab === 'ocr' ? 'active' : ''}`} onClick={() => setPreviewTab('ocr')}>
                  📄 Local OCR &amp; Layout
                </button>
              </div>
            </div>

            <div className="preview-body">
              {previewTab === 'invoice' && (
                <>
                  <div className="preview-card-col">
                    <h4><span>📑</span> Input: Invoice_2026_Global.pdf</h4>
                    <div className="preview-meta-row"><span>Document Type:</span><strong>PDF / Scanned Form</strong></div>
                    <div className="preview-meta-row"><span>Processing Pipeline:</span><strong>Local Tesseract 5 + Layout Parser</strong></div>
                    <div className="preview-meta-row"><span>Owner Security:</span><strong>Isolated Private Media (SQLite3)</strong></div>
                    <div style={{ marginTop: '12px' }}>
                      <span className="tag-badge">Multi-Currency</span>
                      <span className="tag-badge">Line Items Itemized</span>
                      <span className="tag-badge">Status Auditable</span>
                    </div>
                  </div>
                  <div className="preview-card-col">
                    <h4><span>⚡</span> Extracted Financial Structure</h4>
                    <div className="preview-code-block">
{`{
  "supplier": "ACME Industrial Supplies Ltd.",
  "invoice_number": "INV-2026-0894",
  "due_date": "2026-11-15",
  "total": "14,250.00",
  "currency": "USD",
  "line_items_count": 3,
  "confidence_score": 0.98,
  "validation_status": "audited_pass"
}`}
                    </div>
                  </div>
                </>
              )}

              {previewTab === 'qa' && (
                <>
                  <div className="preview-card-col">
                    <h4><span>❓</span> Query: "What is the return eligibility window?"</h4>
                    <p style={{ fontSize: '13px', color: '#9cb1c9', lineHeight: '1.6' }}>
                      Hybrid semantic search executes locally using E5 embeddings cross-referenced against exact BM25 keyword chunks.
                    </p>
                    <div style={{ marginTop: '14px' }}>
                      <span className="tag-badge">Hybrid Mode</span>
                      <span className="tag-badge">Chunk #18</span>
                      <span className="tag-badge">Page 4 Citation</span>
                    </div>
                  </div>
                  <div className="preview-card-col">
                    <h4><span>🎯</span> Verified Supporting Passage</h4>
                    <div className="preview-code-block" style={{ color: '#bae6fd' }}>
{`"Supporting Evidence [Page 4 · Chunk 18]:
Refund claims for damaged shipments must be
submitted within 30 days of bill of lading delivery.
All returned items must include original RMA slip."`}
                    </div>
                  </div>
                </>
              )}

              {previewTab === 'ocr' && (
                <>
                  <div className="preview-card-col">
                    <h4><span>⚙️</span> Local Windows Tesseract OCR</h4>
                    <div className="preview-meta-row"><span>OCR Engine:</span><strong>Tesseract v5.x (Native Host)</strong></div>
                    <div className="preview-meta-row"><span>Language Mode:</span><strong>English (eng)</strong></div>
                    <div className="preview-meta-row"><span>Network Access:</span><strong>Air-Gapped (Zero Outbound)</strong></div>
                    <div style={{ marginTop: '14px' }}>
                      <span className="tag-badge">Offline CPU</span>
                      <span className="tag-badge">UTF-8 Normalized</span>
                    </div>
                  </div>
                  <div className="preview-card-col">
                    <h4><span>📊</span> OCR Telemetry &amp; Ingestion</h4>
                    <div className="preview-code-block">
{`[OCR Engine Stream]:
Ingesting: vendor_receipt_oct26.png
Image Dimensions: 2480 x 3508 px (300 DPI)
Text Extracted: 2,148 characters across 1 page
Bounding Boxes Generated: 42
Media Encapsulation: private_media/ (No Public URL)`}
                    </div>
                  </div>
                </>
              )}
            </div>
          </section>

          {/* 3-Step Lifecycle Workflow */}
          <section className="workflow-strip" id="workflow">
            <h3>Three-Step Document Lifecycle</h3>
            <div className="workflow-steps-grid">
              <div className="workflow-step-card">
                <span className="step-num">Step 01</span>
                <h4>Account Registration</h4>
                <p>Create an owner-isolated account on this local instance. Credentials and access tokens are strictly bound in SQLite3.</p>
              </div>
              <div className="workflow-step-card">
                <span className="step-num">Step 02</span>
                <h4>Session Login</h4>
                <p>Authenticate via CSRF-protected Lax session cookies with idle timeout rotation and rate-limited brute-force guards.</p>
              </div>
              <div className="workflow-step-card">
                <span className="step-num">Step 03</span>
                <h4>Intelligent Dashboard</h4>
                <p>Upload documents, extract text with local OCR, parse invoice line items, and run hybrid semantic search with cited evidence.</p>
              </div>
            </div>
          </section>

          {/* Core Capabilities */}
          <section className="features-section" id="capabilities">
            <h2>Core Platform Capabilities</h2>
            <p className="section-subtitle">
              DocuPilot AI brings enterprise-grade document intelligence to a zero-cloud-leakage, fully local installation.
            </p>
            <div className="features-grid">
              <div className="feature-card">
                <div className="feature-card-icon">📄</div>
                <h3>Local OCR &amp; Private Storage</h3>
                <p>Processes PDF, TXT, PNG, and JPEG files using local Tesseract OCR. Documents are stored in private media roots with no public URLs.</p>
                <div className="feature-tags">
                  <span className="feature-tag">Tesseract OCR</span>
                  <span className="feature-tag">Private Storage</span>
                  <span className="feature-tag">Zero Cloud Leak</span>
                </div>
              </div>
              <div className="feature-card">
                <div className="feature-card-icon">🧾</div>
                <h3>Invoice Intelligence</h3>
                <p>Automatically derives totals, currencies, suppliers, due dates, and itemized line items with owner-audited payment lifecycle tracking.</p>
                <div className="feature-tags">
                  <span className="feature-tag">Line Items Parser</span>
                  <span className="feature-tag">Multi-Currency</span>
                  <span className="feature-tag">Due Dates</span>
                </div>
              </div>
              <div className="feature-card">
                <div className="feature-card-icon">🔍</div>
                <h3>Evidence-Grounded Q&amp;A</h3>
                <p>Keyword, multilingual semantic, and hybrid retrieval modes quote exact source passages and page numbers without hallucination.</p>
                <div className="feature-tags">
                  <span className="feature-tag">Hybrid Search</span>
                  <span className="feature-tag">Multilingual E5</span>
                  <span className="feature-tag">PDF Citations</span>
                </div>
              </div>
              <div className="feature-card">
                <div className="feature-card-icon">👥</div>
                <h3>Human-in-the-Loop Review</h3>
                <p>Confidence scores, classification reviews, and operator review queues ensure automated AI suggestions are verifiable by humans.</p>
                <div className="feature-tags">
                  <span className="feature-tag">Audit Triage</span>
                  <span className="feature-tag">Confidence Metrics</span>
                  <span className="feature-tag">Reliability Board</span>
                </div>
              </div>
            </div>
          </section>

          {/* Security & Compliance Spotlight */}
          <section className="security-spotlight" id="security">
            <h3>Enterprise Privacy &amp; Deployment Security</h3>
            <p className="lead">Built to adhere strictly to local-first data protection standards and defensive deployment baselines.</p>
            <div className="security-grid">
              <div className="security-item">
                <strong>🔒 Private Media Isolation</strong>
                <span>Documents are stored in a dedicated private media folder with <code>MEDIA_URL = None</code>. Access requires authenticated socket streaming.</span>
              </div>
              <div className="security-item">
                <strong>🛡️ Hardened Session Cookies</strong>
                <span>CSRF protection and HttpOnly session cookies replace vulnerable recurring Basic Auth headers and browser token stores.</span>
              </div>
              <div className="security-item">
                <strong>⚡ Lockout &amp; Rate Limiting</strong>
                <span>Database-backed rate limiting enforces 5-attempt thresholds per IP/user bucket within 15-minute sliding windows.</span>
              </div>
              <div className="security-item">
                <strong>👤 Strict Tenant Boundaries</strong>
                <span>Every database query is scoped to document ownership. Cross-user document or invoice requests return clean HTTP 404 responses.</span>
              </div>
            </div>
          </section>

          {/* Technical FAQ */}
          <section className="faq-section" id="faq">
            <h2>Frequently Asked Questions</h2>
            <div className="faq-grid">
              <div className="faq-card">
                <h4>Can DocuPilot AI run completely offline?</h4>
                <p>Yes. The entire processing pipeline—including Django backend, SQLite3 database, React frontend, and Tesseract OCR—runs 100% on your local Windows workstation with zero internet dependencies.</p>
              </div>
              <div className="faq-card">
                <h4>How are documents protected from other users?</h4>
                <p>All database models and file endpoints are filtered strictly by the authenticated user's ID at the ORM layer. Other users cannot enumerate, inspect, or download documents they do not own.</p>
              </div>
              <div className="faq-card">
                <h4>What file formats are supported?</h4>
                <p>DocuPilot natively supports PDF documents, UTF-8 TXT files, and PNG/JPEG images up to 10 MiB with automatic resolution and orientation normalization.</p>
              </div>
            </div>
          </section>

          <footer className="home-footer">
            <div>
              <strong>DocuPilot AI</strong> · Developed by Tech_Innovators · MIT License.
            </div>
            <div>
              Private &amp; On-Premises Architecture · Local SQLite3 Baseline
            </div>
          </footer>
        </main>
      </div>
    );
  }

  return <div className="app-shell"><aside className="sidebar"><div className="brand"><span className="brand-icon">D</span><span>DocuPilot <b>AI</b></span></div><p className="sidebar-label">WORKSPACE</p><nav aria-label="Primary navigation">{nav.map(([key,label]) => <button key={key} onClick={() => setTab(key)} className={`nav-item ${tab === key ? 'active' : ''}`}>{label}</button>)}</nav><div className="sidebar-bottom"><span>Signed in as <strong>{credentials.username}</strong></span><button className="ghost" onClick={logout}>Sign out</button></div></aside><main className="main-panel"><header className="topbar"><div><span className="eyebrow">TECH_INNOVATORS / DOCUPILOT AI</span><h1>{nav.find(([key]) => key === tab)?.[1]}</h1></div><span className="environment-tag">SQLite3 · MVP</span></header><div className="main-content">
  {tab === 'documents' && <><div className="intro"><h2>Document library</h2><p>Upload PDF, UTF-8 TXT, PNG or JPEG files (10 MiB maximum). Scanned pages use local OCR. Private documents are accessible only to their owner.</p></div><div className="panel"><h3>Upload document</h3><form onSubmit={upload} className="upload-form"><label>Document title (optional)<input maxLength={255} value={title} onChange={e => setTitle(e.target.value)} placeholder="e.g. Supplier invoice October" /></label><label>Choose PDF, TXT or image<input type="file" accept=".pdf,.txt,.png,.jpg,.jpeg,application/pdf,text/plain,image/png,image/jpeg" required onChange={e => setFile(e.target.files?.[0] || null)} /></label><button className="primary" disabled={uploadBusy || !file}>{uploadBusy ? 'Uploading…' : 'Upload document'}</button></form></div>{processingJob && <AsyncJobPanel job={processingJob} auth={credentials} onClose={() => setProcessingJob(null)} onUpdate={setProcessingJob} onComplete={() => { loadDocs(credentials); setPages(null); setAnswer(null); }} />}
<Message text={documentError} kind="error" onClose={() => setDocumentError('')}/><Message text={message} onClose={() => setMessage('')}/><div className="panel"><div className="panel-heading"><h3>Your documents</h3><button className="secondary" onClick={() => loadDocs(credentials)} disabled={documentsBusy}>Refresh</button></div>{documentsBusy ? <p role="status">Loading documents…</p> : documents.length === 0 ? <div className="empty-state">No documents yet. Upload a PDF, TXT or image file to begin.</div> : <div className="document-list">{documents.map(doc => <article className="document-item" key={doc.id}><div><h4>{doc.title}</h4><p>Classification: {classificationLabel(doc.classification_category)}</p><p>{(doc.file_type || 'file').toUpperCase()} · {doc.processing_status} · {doc.original_filename || 'metadata only'}</p></div><div className="actions"><button disabled={busyId === doc.id || !doc.has_file} onClick={() => documentAction(doc, 'extract')}>Extract text</button><button disabled={busyId === doc.id || !doc.has_file} onClick={() => documentAction(doc, 'extract-async')}>Background extract</button><button disabled={busyId === doc.id} onClick={() => documentAction(doc, 'pages')}>View pages</button><button disabled={busyId === doc.id || doc.processing_status !== 'completed'} onClick={() => documentAction(doc, 'invoice')}>Extract invoice</button><button className="danger" disabled={busyId === doc.id} onClick={() => documentAction(doc, 'delete')}>Delete</button></div><ClassificationPanel document={doc} auth={credentials} onUpdated={() => loadDocs(credentials)} /><ClassificationReview document={doc} auth={credentials} /></article>)}</div>}</div>{pages && <section className="panel"><div className="panel-heading"><h3>Extracted pages · {pages.document.title}</h3><button className="secondary" onClick={() => setPages(null)}>Close</button></div>{pages.items.length === 0 ? <p className="muted">No text extracted yet.</p> : pages.items.map(page => <div className="page-excerpt" key={page.id}><strong>Page {page.page_number}</strong><pre>{page.extracted_text}</pre></div>)}</section>}</>}
  {tab === 'reviews' && <ReviewQueue auth={credentials} />}
  {tab === 'analytics' && <AnalyticsDashboard auth={credentials} />}
  {tab === 'classification-quality' && <ClassificationQuality auth={credentials} />}
  {tab === 'feedback-quality' && <FeedbackQuality auth={credentials} />}
  {tab === 'reliability' && <ReliabilityDashboard auth={credentials} />}
  {tab === 'invoices' && <><div className="intro"><h2>Invoice intelligence</h2><p>Due dates and balances are derived from extracted documents. Payment status is manually confirmed by the document owner.</p></div><Message text={invoiceError} kind="error" onClose={() => setInvoiceError('')}/><div className="metrics"><Card label="Extracted invoices" value={summary?.invoice_count ?? '—'} /><Card label="Pending" value={summary?.payment_status_counts?.pending ?? '—'} /><Card label="Overdue pending" value={summary?.overdue_pending_count ?? '—'} /><Card label="Unconfirmed past due" value={summary?.past_due_unconfirmed_count ?? '—'} /></div><div className="panel"><h3>Pending totals by currency</h3><div className="currency-row">{summary && Object.keys(summary.pending_totals_by_currency || {}).length ? Object.entries(summary.pending_totals_by_currency).map(([currency, amount]) => <span className="currency-chip" key={currency}>{currency} <strong>{amount}</strong></span>) : <span className="muted">No confirmed pending balances.</span>}</div><p className="footnote">Missing or invalid amounts are excluded, never treated as zero. {summary?.pending_without_usable_total_count ?? 0} pending invoices excluded.</p></div><div className="panel"><form className="filters" onSubmit={refreshInvoices}><label>Payment status<select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}><option value="">All statuses</option>{statuses.map(s => <option key={s}>{s}</option>)}</select></label><label>Due category<select value={dueFilter} onChange={e => setDueFilter(e.target.value)}><option value="">All due dates</option>{['overdue','due_today','upcoming','undated','past_due_unconfirmed'].map(s => <option key={s} value={s}>{s.replaceAll('_',' ')}</option>)}</select></label><button className="secondary" disabled={invoiceBusy}>Apply filters</button><button type="button" className="primary" disabled={busyId === 'csv'} onClick={exportInvoices}>Export CSV</button></form><div className="panel-heading"><h3>Invoice records</h3><span className="muted">{invoices.length} matching records</span></div>{invoiceBusy ? <p role="status">Loading invoice report…</p> : !invoices.length ? <div className="empty-state">No invoices match these filters. Extract invoice fields from a processed document first.</div> : <div className="table-wrap"><table><thead><tr><th>Invoice</th><th>Supplier</th><th>Due date</th><th>Total</th><th>Due category</th><th>Payment status</th><th>Details</th></tr></thead><tbody>{invoices.map(row => <tr key={row.record_id}><td><strong>{row.invoice_number || 'Unverified'}</strong><small>{row.document_title}</small></td><td>{row.supplier || '—'}</td><td>{row.due_date || '—'}</td><td>{row.total ? `${row.currency || '?'} ${row.total}` : '—'}</td><td>{row.due_category?.replaceAll('_', ' ')}</td><td><select aria-label={`Payment status for invoice ${row.record_id}`} disabled={busyId === `invoice-${row.record_id}`} value={row.payment_status} onChange={e => changePayment(row.record_id, e.target.value)}>{statuses.map(s => <option key={s}>{s}</option>)}</select></td><td><button type="button" className="secondary" disabled={lineItemBusy} onClick={() => showLineItems(row.record_id)}>Line items</button></td></tr>)}</tbody></table></div>}{lineItemBusy && <p role="status">Loading line items…</p>}{lineItemView && <div className="line-items-panel"><div className="panel-heading"><h3>Invoice {lineItemView.recordId} · Line items</h3><button className="secondary" onClick={() => setLineItemView(null)}>Close</button></div>{lineItemView.items.length === 0 ? <p>No confidently recognized line-item rows. Review the original invoice.</p> : <div className="table-wrap"><table><thead><tr><th>Description</th><th>Quantity</th><th>Unit price</th><th>Line total</th><th>Validation</th><th>Source page</th></tr></thead><tbody>{lineItemView.items.map(item => <tr key={item.line_number}><td title={item.source_excerpt}>{item.description}</td><td>{item.quantity}</td><td>{item.unit_price}</td><td>{item.line_total}</td><td>{item.validation_status}</td><td>Page {item.page_number}</td></tr>)}</tbody></table></div>}<p className="footnote">Automatically extracted rows are unreviewed; verify against the original document.</p></div>}</div></>}
  {tab === 'ask' && <><div className="intro"><h2>Ask your documents</h2><p>Find document evidence using keyword, semantic or hybrid retrieval. Answers quote source passages—not generated claims.</p></div><div className="panel"><form onSubmit={submitQuestion} className="form-stack"><label>Your question<textarea maxLength={500} required rows={3} value={question} onChange={e => setQuestion(e.target.value)} placeholder="What does the refund policy say?" /></label><label>Retrieval method<select aria-label="Retrieval method" value={retrievalMode} onChange={e => setRetrievalMode(e.target.value)}><option value="keyword">Keyword (fast, offline)</option><option value="semantic">Semantic (local multilingual model)</option><option value="hybrid">Hybrid (semantic + keyword)</option></select></label><fieldset className="doc-selector"><legend>Search scope</legend><p className="muted">Select documents, or leave all unchecked to search every indexed document you own.</p><div className="selector-options">{documents.length ? documents.map(doc => <label key={doc.id} className="check-row"><input type="checkbox" checked={selectedDocs.includes(doc.id)} onChange={e => setSelectedDocs(prev => e.target.checked ? [...prev, doc.id] : prev.filter(id => id !== doc.id))} />{doc.title}</label>) : <span className="muted">No documents uploaded</span>}</div></fieldset><button className="primary" disabled={asking || !question.trim()}>{asking ? 'Searching evidence…' : 'Ask documents'}</button></form></div><Message text={askError} kind="error" onClose={() => setAskError('')}/>{answer && <section className="panel" aria-live="polite"><h3>{answer.has_evidence ? 'Evidence-based answer' : 'Insufficient evidence'}</h3><p className="answer-text">{answer.answer}</p>{answer.has_evidence && <><h4 className="sources-heading">Supporting sources</h4>{(answer.source_references || []).map((ref,i) => <div className="source" key={`${ref.chunk_id}-${i}`}><strong>{ref.document_title} · Page {ref.page_number}</strong><p>{ref.excerpt}</p><small>Document #{ref.document_id} · Chunk #{ref.chunk_id} · {ref.retrieval_method || "keyword"}</small>{documents.find(d => d.id === ref.document_id)?.file_type?.toLowerCase() === 'pdf' && <button type="button" className="secondary" onClick={() => setPdfEvidence(ref)}>View highlighted PDF · page {ref.page_number}</button>}</div>)}</>}{pdfEvidence && <EvidenceViewer evidence={pdfEvidence} auth={credentials} onClose={() => setPdfEvidence(null)} />}<p className="footnote">Extractive search only. Verify supporting passages against their original documents.</p></section>}</>}
</div></main></div>;
}
