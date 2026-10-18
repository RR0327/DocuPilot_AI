import { useEffect, useState } from 'react';
import { api } from './api.js';
import { nextPoll, isTerminal } from './processing.js';

/** Polls only while mounted and while a job is active; never stores credentials. */
export default function AsyncJobPanel({ job, auth, onUpdate, onComplete, onClose }) {
  const [error, setError] = useState('');
  const [retrying, setRetrying] = useState(false);
  useEffect(() => {
    if (!job?.id || isTerminal(job.state)) return;
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      try {
        const latest = await api(`/processing-jobs/${job.id}/`, auth, { signal: controller.signal });
        if (!controller.signal.aborted) {
          onUpdate({ ...latest, document_title: job.document_title });
          if (latest.state === 'succeeded') onComplete();
        }
      } catch (exc) { if (!controller.signal.aborted) setError(exc.message); }
    }, nextPoll(job.state));
    return () => { clearTimeout(timer); controller.abort(); };
  }, [job?.id, job?.state, job?.started_at, auth, onUpdate, onComplete]);

  async function retry() {
    setRetrying(true); setError('');
    try {
      const fresh = await api(`/processing-jobs/${job.id}/retry/`, auth, { method: 'POST' });
      onUpdate({ ...fresh, document_title: job.document_title });
    } catch (exc) { setError(exc.message); }
    finally { setRetrying(false); }
  }
  return <section className="panel" aria-live="polite">
    <div className="panel-heading"><h3>Background extraction — {job.document_title}</h3><button className="secondary" onClick={onClose}>Close</button></div>
    <p role="status">Status: <strong>{job.state}</strong> · Attempt {job.attempt}{job.state === 'running' ? ' · Processing document…' : ''}</p>
    {job.state === 'queued' && <p className="muted">Waiting for the Redis worker. If this persists, check the worker terminal.</p>}
    {job.state === 'succeeded' && <p>Completed: {job.page_count} page(s), {job.character_count} characters.</p>}
    {job.state === 'failed' && <><p role="alert">{job.error_message || 'Extraction failed'}</p><button className="secondary" disabled={retrying} onClick={retry}>{retrying ? 'Retrying…' : 'Retry failed job'}</button></>}
    {error && <p role="alert">Unable to refresh job status: {error} <button className="secondary" onClick={() => onUpdate({ ...job })}>Try again</button></p>}
  </section>;
}
