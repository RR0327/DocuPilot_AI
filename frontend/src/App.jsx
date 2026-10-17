import { useEffect, useState } from 'react';
export default function App() {
  const [status, setStatus] = useState('Checking backend…');
  useEffect(() => {
    const controller = new AbortController();
    fetch('/api/health/', { signal: controller.signal })
      .then((response) => { if (!response.ok) throw new Error('Backend unavailable'); return response.json(); })
      .then((data) => setStatus(data.status === 'ok' ? 'Backend connected' : 'Unexpected backend response'))
      .catch((error) => { if (error.name !== 'AbortError') setStatus('Backend disconnected'); });
    return () => controller.abort();
  }, []);
  return <main className="min-h-screen bg-slate-950 text-white flex items-center justify-center p-6"><section className="max-w-xl w-full rounded-2xl bg-slate-900 border border-slate-700 p-10 shadow-xl"><div className="text-sm tracking-widest uppercase text-sky-400">Document intelligence platform</div><h1 className="text-4xl font-bold mt-3">DocuPilot AI</h1><p className="text-slate-300 mt-4">Phase 0 · Step 1 — Development foundation</p><p role="status" className="mt-8 rounded-lg bg-slate-800 p-4">API status: {status}</p><p className="text-slate-400 text-sm mt-5">Document upload and AI capabilities arrive in later steps.</p></section></main>;
}
