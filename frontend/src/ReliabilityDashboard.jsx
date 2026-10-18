import {useEffect,useState} from 'react';
import {api} from './api.js';
import {triageRows,validateReliability} from './reliability.js';
export default function ReliabilityDashboard({auth}) {
 const [report,setReport]=useState(null);const [error,setError]=useState('');
 useEffect(()=>{let active=true;api('/classification/reliability/',auth).then(r=>{if(active){if(!validateReliability(r))throw new Error('Unexpected reliability report');setReport(r);}}).catch(e=>{if(active)setError(e.message)});return()=>{active=false}},[auth]);
 return <section className="panel" aria-label="Classification reliability">
 <h2>Classification reliability and error triage</h2>
 <p className="footnote">Owner feedback is operational review, not independent ground truth or measured classifier accuracy.</p>
 {error&&<p role="alert" className="notice notice-error">{error}</p>}
 {!report&&!error&&<p role="status">Loading reliability report…</p>}
 {report&&<><p>Reviewed documents: {report.reviewed_document_count}</p>
 <div className="table-wrap"><table><caption>Review-related cases requiring attention</caption><thead><tr><th>Issue</th><th>Count</th></tr></thead><tbody>
 {triageRows(report).map(row=><tr key={row.key}><th scope="row">{row.key.replaceAll('_',' ')}</th><td>{row.count}</td></tr>)}
 </tbody></table></div><p className="footnote">Independent evaluation is available as an offline management command using separately adjudicated documents. No private pages are uploaded by this screen.</p></>}
 </section>;
}
