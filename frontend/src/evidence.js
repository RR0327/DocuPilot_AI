/** Escape both document and evidence strings before react-pdf inserts HTML text spans. */
export function escapeHtml(value) { return String(value).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch])); }
export function highlightText(text, evidence) {
  if (typeof text !== 'string') return '';
  const tokens = [...new Set(String(evidence || '').match(/[\p{L}\p{N}]{4,}/gu) || [])].slice(0, 30);
  if (!tokens.length) return escapeHtml(text);
  const escaped = tokens.map(v => v.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  const pattern = new RegExp(`(${escaped.join('|')})`, 'giu');
  return text.split(pattern).map(part => tokens.some(t => t.toLocaleLowerCase() === part.toLocaleLowerCase()) ? `<mark class="pdf-evidence-highlight">${escapeHtml(part)}</mark>` : escapeHtml(part)).join('');
}
