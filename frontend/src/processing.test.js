import test from 'node:test';
import assert from 'node:assert/strict';
import { isTerminal, nextPoll } from './processing.js';
import { api } from './api.js';

test('polling continues for active jobs and stops for terminal jobs', () => {
  assert.equal(nextPoll('queued'), 2000);
  assert.equal(nextPoll('running'), 2000);
  assert.equal(nextPoll('succeeded'), 0);
  assert.equal(isTerminal('failed'), true);
});
test('background request is authenticated and returns job UUID', async () => {
  const original = globalThis.fetch;
  try {
    globalThis.fetch = async (url, opts) => {
      assert.equal(url, '/api/documents/9/extract-async/');
      assert.equal(opts.method, 'POST');
      assert.equal(opts.headers.Authorization, undefined);
      assert.equal(opts.credentials, 'include');
      return { ok: true, status: 202, json: async () => ({ id: '9a', state: 'queued' }) };
    };
    assert.equal((await api('/documents/9/extract-async/', { username: 'u', mode: 'session' }, { method: 'POST' })).state, 'queued');
  } finally { globalThis.fetch = original; }
});
test('retry and polling URLs are owner-authenticated', async () => {
  const original = globalThis.fetch;
  try {
    const urls = [];
    globalThis.fetch = async (url, opts) => {
      urls.push(url); assert.equal(opts.headers.Authorization, undefined);
      assert.equal(opts.credentials, 'include');
      return { ok: true, status: 200, json: async () => ({ state: 'running' }) };
    };
    const user = { username: 'u', mode: 'session' };
    await api('/processing-jobs/abcdef/', user);
    await api('/processing-jobs/abcdef/retry/', user, { method: 'POST' });
    assert.deepEqual(urls, ['/api/processing-jobs/abcdef/', '/api/processing-jobs/abcdef/retry/']);
  } finally { globalThis.fetch = original; }
});
