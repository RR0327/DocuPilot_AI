import { useEffect, useMemo, useState } from 'react';
import { Document as PDFDocument, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/TextLayer.css';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import { privatePdf } from './api.js';
import { highlightText } from './evidence.js';

pdfjs.GlobalWorkerOptions.workerSrc = new URL('pdfjs-dist/build/pdf.worker.min.mjs', import.meta.url).toString();

/** Binary preview is fetched only after authorization and released when the viewer closes. */
export default function EvidenceViewer({ evidence, auth, onClose }) {
  const [url, setUrl] = useState(null);
  const [error, setError] = useState('');
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(evidence.page_number);
  useEffect(() => {
    let active = true; let currentUrl = null;
    setUrl(null); setError(''); setCount(0); setPage(evidence.page_number);
    privatePdf(evidence.document_id, auth).then(blob => {
      if (!active) return;
      currentUrl = URL.createObjectURL(blob); setUrl(currentUrl);
    }).catch(err => { if (active) setError(err.message); });
    return () => { active = false; if (currentUrl) URL.revokeObjectURL(currentUrl); };
  }, [auth, evidence.document_id, evidence.page_number]);
  const renderer = useMemo(() => ({ str }) => highlightText(str, evidence.excerpt), [evidence.excerpt]);
  const validPage = Math.max(1, Math.min(page, count || page));
  return <section className="evidence-viewer" aria-label="PDF evidence viewer">
    <div className="panel-heading"><h3>Source PDF · {evidence.document_title}</h3><button type="button" className="secondary" onClick={onClose}>Close PDF</button></div>
    <p className="muted">Evidence is from page {evidence.page_number}. Highlighted words are approximate text-layer matches, not verified bounding boxes. Scanned/OCR-only pages may have no highlight overlay.</p>
    <blockquote className="evidence-excerpt">{evidence.excerpt}</blockquote>
    {error && <p role="alert">{error}</p>}
    {!url && !error && <p role="status">Loading private PDF…</p>}
    {url && <><div className="pdf-controls"><button type="button" disabled={validPage <= 1} onClick={() => setPage(p => Math.max(1,p-1))}>Previous page</button><span>Page {validPage} of {count || '…'}</span><button type="button" disabled={!count || validPage >= count} onClick={() => setPage(p => Math.min(count,p+1))}>Next page</button><button type="button" onClick={() => setPage(evidence.page_number)} disabled={validPage === evidence.page_number}>Go to evidence page</button></div>
      <div className="pdf-canvas"><PDFDocument file={url} onLoadSuccess={({numPages}) => setCount(numPages)} onLoadError={err => setError(`PDF rendering failed: ${err.message}`)} loading="Rendering PDF…"><Page pageNumber={validPage} width={Math.min(720, typeof window === 'undefined' ? 700 : Math.max(300, window.innerWidth - 140))} renderAnnotationLayer={false} renderTextLayer customTextRenderer={renderer} /></PDFDocument></div>
    </>}
    <p className="footnote">OCR evidence is displayed above the page even when no text-layer coordinates exist. Confirm it visually against the scan.</p>
  </section>;
}
