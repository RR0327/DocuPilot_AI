import test from 'node:test';
import assert from 'node:assert/strict';
import { basicHeader, queryString, documentList, allDocuments, validateUpload, api } from './api.js';

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

test('document pagination collects every page and respects per-page request paths', async () => {
  const called=[];
  const result=await allDocuments({username:'u',password:'p'}, async path => {
    called.push(path);
    return path==='/documents/' ? {results:[{id:1}],next:'http://127.0.0.1:8000/api/documents/?page=2'} : {results:[{id:2}],next:null};
  });
  assert.deepEqual(result.map(d=>d.id),[1,2]);
  assert.deepEqual(called,['/documents/','/documents/?page=2']);
});
test('document pagination blocks cross-origin next URL and loops', async () => {
  await assert.rejects(allDocuments({},async()=>({results:[],next:'https://evil.test/api/documents/?page=2'})),/Unexpected pagination destination/);
  await assert.rejects(allDocuments({},async()=>({results:[],next:'/api/documents/'})),/Invalid document pagination response/);
});
test('client upload validation matches server size and extensions', () => {
  assert.match(validateUpload(null),/Select/);
  assert.match(validateUpload({name:'x.exe',size:3}),/Only PDF/);
  assert.match(validateUpload({name:'x.pdf',size:0}),/between/);
  assert.match(validateUpload({name:'x.pdf',size:10*1024*1024+1}),/between/);
  assert.equal(validateUpload({name:'x.PDF',size:100}),'');
});


test('validates OCR image uploads', () => {
  assert.equal(validateUpload({ name: 'scan.png', size: 1024 }), '');
  assert.equal(validateUpload({ name: 'photo.jpeg', size: 2048 }), '');
  assert.match(validateUpload({ name: 'bad.webp', size: 1024 }), /Only PDF/);
});
