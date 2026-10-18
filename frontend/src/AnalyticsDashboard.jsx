import { useEffect, useState } from 'react';
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { api } from './api.js';
import { currencySeries, supplierSeries } from './analytics.js';

const currencyCodes = ['BDT', 'USD', 'EUR', 'GBP'];

export default function AnalyticsDashboard({ auth }) {
  const [currency, setCurrency] = useState('BDT');
  const [year, setYear] = useState('');
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    if (!auth) return;
    const controller = new AbortController();
    setBusy(true); setError(''); setData(null);
    const params = new URLSearchParams({currency, limit:'10'});
    if (year) params.set('year', year);
    api(`/invoices/analytics/?${params}`, auth, {signal:controller.signal})
      .then(result => { if (!controller.signal.aborted) setData(result); })
      .catch(err => { if (!controller.signal.aborted) setError(err.message); })
      .finally(() => { if (!controller.signal.aborted) setBusy(false); });
    return () => controller.abort();
  }, [auth, currency, year, revision]);
  const months = currencySeries(data, currency);
  const suppliers = supplierSeries(data, currency);
  return <section aria-label="Supplier analytics" className="analytics-workspace">
    <div className="intro"><h2>Supplier analytics</h2><p>Invoice-value trends by supplier and month. These are not verified cash expenditure or payment dates.</p></div>
    <div className="panel analytics-controls">
      <label>Currency<select aria-label="Analytics currency" value={currency} onChange={e=>setCurrency(e.target.value)}>{currencyCodes.map(code=><option key={code} value={code}>{code}</option>)}</select></label>
      <label>Invoice year<select aria-label="Analytics year" value={year} onChange={e=>setYear(e.target.value)}><option value="">All years</option>{Array.from({length:8},(_,i)=>2023+i).map(n=><option key={n} value={n}>{n}</option>)}</select></label>
      <button className="secondary" onClick={()=>setRevision(n=>n+1)} disabled={busy}>Refresh analytics</button>
    </div>
    {busy && <p role="status">Loading supplier analytics…</p>}
    {error && <p role="alert">{error}</p>}
    {data && <>
      <div className="metrics"><div className="metric"><p>Included invoices</p><strong>{data.included_invoice_count}</strong></div><div className="metric"><p>Invoice value ({currency})</p><strong>{data.totals_by_currency?.[currency] ?? '0.00'}</strong></div><div className="metric"><p>Suppliers</p><strong>{data.supplier_count}</strong></div></div>
      <div className="analytics-grid">
        <div className="panel"><h3>Monthly invoice value · {currency}</h3>{months.length ? <div className="analytics-chart" role="img" aria-label="Monthly invoice value line chart"><ResponsiveContainer width="100%" height="100%"><LineChart data={months}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="month"/><YAxis/><Tooltip/><Line type="monotone" dataKey="amount" stroke="#2563eb" strokeWidth={2}/></LineChart></ResponsiveContainer></div> : <p>No dated invoices for this currency and year.</p>}</div>
        <div className="panel"><h3>Top suppliers · {currency}</h3>{suppliers.length ? <div className="analytics-chart" role="img" aria-label="Supplier invoice value bar chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={suppliers} layout="vertical" margin={{left:25}}><CartesianGrid strokeDasharray="3 3"/><XAxis type="number"/><YAxis type="category" dataKey="supplier" width={110}/><Tooltip/><Bar dataKey="amount" fill="#2563eb"/></BarChart></ResponsiveContainer></div> : <p>No qualifying suppliers for this currency.</p>}</div>
      </div>
      <div className="panel"><h3>Included supplier values</h3><div className="table-wrap"><table><thead><tr><th>Supplier</th><th>Currency</th><th>Invoice value</th></tr></thead><tbody>{suppliers.map(row=><tr key={row.supplier}><td>{row.supplier}</td><td>{currency}</td><td>{row.amount.toFixed(2)}</td></tr>)}</tbody></table></div><p className="footnote">Excluded records: {Object.entries(data.excluded_invoice_counts || {}).map(([reason,count])=>`${reason}: ${count}`).join(' · ') || 'None'}. Rejected invoices, missing values and unsupported currencies are not added to totals. Reviewed corrections apply only while approved.</p></div>
    </>}
  </section>;
}
