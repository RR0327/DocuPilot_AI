import test from 'node:test';
import assert from 'node:assert/strict';
import {csrfCookie, api} from './api.js';

test('csrf cookie extraction uses exact name, not adjacent cookies', () => {
  assert.equal(csrfCookie('xcsrftoken=fake; csrftoken=good%20token; sessionid=secret'), 'good token');
  assert.equal(csrfCookie('sessionid=secret'), '');
});

test('session requests do not send Basic credentials and include CSRF on writes', async () => {
  const original = globalThis.fetch;
  const originalDoc = globalThis.document;
  let request;
  globalThis.document = {cookie:'csrftoken=abc123; sessionid=SECRET'};
  globalThis.fetch = async (url, options) => {request = {url,options}; return {ok:true,status:200,json:async()=>({ok:true})};};
  try {
    await api('/documents/', {username:'alice',mode:'session'}, {method:'POST',body:{hello:'world'}});
    assert.equal(request.options.headers['X-CSRFToken'],'abc123');
    assert.equal(request.options.headers.Authorization, undefined);
    assert.equal(request.options.credentials,'same-origin');
  } finally {globalThis.fetch = original;globalThis.document = originalDoc;}
});
