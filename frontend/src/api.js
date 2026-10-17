/** HTTP Basic is supported by the existing backend. Credentials stay in React memory. */
export function basicHeader(username, password) {
  const bytes = new TextEncoder().encode(`${username}:${password}`);
  let binary = '';
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return `Basic ${btoa(binary)}`;
}

export function queryString(filters = {}) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== null && value !== '') search.set(key, String(value));
  }
  return search.toString();
}

export async function api(path, auth, options = {}) {
  const { method = 'GET', body, signal, download = false } = options;
  const headers = { Authorization: basicHeader(auth.username, auth.password) };
  if (body !== undefined && !(body instanceof FormData)) headers['Content-Type'] = 'application/json';
  let response;
  try {
    response = await fetch(`/api${path}`, { method, headers, body: body instanceof FormData ? body : body === undefined ? undefined : JSON.stringify(body), signal, cache: 'no-store' });
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new Error('Cannot connect to the backend. Start Django on port 8000.');
  }
  if (!response.ok) {
    let detail;
    try {
      const data = await response.json();
      detail = typeof data.detail === 'string' ? data.detail : Object.entries(data).map(([key, val]) => `${key}: ${Array.isArray(val) ? val.join(', ') : JSON.stringify(val)}`).join('; ');
    } catch { detail = response.statusText; }
    if (response.status === 401 || response.status === 403) throw new Error('Authentication failed or access denied. Check your credentials.');
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return download ? response.blob() : response.status === 204 ? null : response.json();
}

/** Collect every owner-scoped document page without changing the backend API. */
export async function allDocuments(auth, request = api) {
  const results = [];
  let path = '/documents/';
  const visited = new Set();
  while (path) {
    if (visited.has(path) || visited.size >= 200) throw new Error('Invalid document pagination response');
    visited.add(path);
    const page = await request(path, auth);
    results.push(...documentList(page));
    if (!page || Array.isArray(page) || !page.next) break;
    const url = new URL(page.next, 'http://localhost');
    if (url.origin !== 'http://localhost' && url.hostname !== '127.0.0.1' && url.hostname !== 'localhost') {
      throw new Error('Unexpected pagination destination');
    }
    if (!url.pathname.startsWith('/api/documents/')) throw new Error('Unexpected document pagination path');
    path = url.pathname.slice(4) + url.search;
  }
  return results;
}

export function validateUpload(file) {
  if (!file) return 'Select a PDF or TXT file.';
  const ext = file.name.split('.').pop().toLowerCase();
  if (!['pdf', 'txt'].includes(ext)) return 'Only PDF and TXT files are supported.';
  if (!file.size || file.size > 10 * 1024 * 1024) return 'File must be between 1 byte and 10 MiB.';
  return '';
}

export function documentList(payload) {
  return Array.isArray(payload) ? payload : Array.isArray(payload?.results) ? payload.results : [];
}

export function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
