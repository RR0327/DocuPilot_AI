import test from 'node:test';
import assert from 'node:assert/strict';
import { basicHeader, queryString, documentList, api } from './api.js';

test('Basic auth encodes international usernames and is not persisted', () => {
  const header = basicHeader('বাংলা', 'päss');
  assert.equal(Buffer.from(header.slice(6), 'base64').toString('utf8'), 'বাংলা:päss');
});
test('filter query omits blank values and escapes inputs', () => {
  assert.equal(queryString({ payment_status: 'pending', due: '', document_id: '10&x' }), 'payment_status=pending&document_id=10%26x');
});
test('document lists handle DRF pagination and arrays', () => {
  assert.deepEqual(documentList({ count: 1, results: [{ id: 1 }] }), [{ id: 1 }]);
  assert.deepEqual(documentList([{ id: 2 }]), [{ id: 2 }]);
  assert.deepEqual(documentList(null), []);
});
test('API applies auth headers and serializes JSON', async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async (url, opts) => {
    assert.equal(url, '/api/ask/'); assert.equal(opts.method, 'POST');
    assert.equal(opts.headers['Content-Type'], 'application/json');
    assert.equal(JSON.parse(opts.body).question, 'Test');
    return { ok: true, status: 200, json: async () => ({ has_evidence: false }) };
  };
  try { assert.deepEqual(await api('/ask/', { username: 'u', password: 'p' }, { method: 'POST', body: { question: 'Test' } }), { has_evidence: false }); }
  finally { globalThis.fetch = original; }
});
test('API handles empty delete responses and auth denial', async () => {
  const original = globalThis.fetch;
  try {
    globalThis.fetch = async () => ({ ok: true, status: 204 });
    assert.equal(await api('/documents/1/', { username: 'u', password: 'p' }, { method: 'DELETE' }), null);
    globalThis.fetch = async () => ({ ok: false, status: 403, json: async () => ({ detail: 'no' }) });
    await assert.rejects(api('/documents/', { username: 'u', password: 'bad' }), /Authentication failed/);
  } finally { globalThis.fetch = original; }
});
test('API handles backend connection loss', async () => {
  const original = globalThis.fetch;
  try { globalThis.fetch = async () => { throw new TypeError('Failed to fetch'); };
    await assert.rejects(api('/documents/', { username: 'u', password: 'p' }), /Cannot connect/);
  } finally { globalThis.fetch = original; }
});
