import test from 'node:test';
import assert from 'node:assert/strict';
import { escapeHtml, highlightText } from './evidence.js';
import { privatePdf } from './api.js';
test('PDF matching escapes untrusted text and highlights evidence words', () => {
  assert.equal(escapeHtml('<script>'), '&lt;script&gt;');
  const output = highlightText('Refund <script> within 30 days', 'Refund within 30 days');
  assert.match(output, /<mark class="pdf-evidence-highlight">Refund<\/mark>/);
  assert.doesNotMatch(output, /<script>/);
});
test('no recognized evidence leaves text unmarked', () => {
  assert.equal(highlightText('Unrelated', ''), 'Unrelated');
});
test('private PDF requests only the authorized path and validates response', async () => {
  const blob = new Blob(['%PDF-test'], { type: 'application/pdf' });
  const result = await privatePdf(12, {}, async (path, auth, opts) => {
    assert.equal(path, '/documents/12/private-pdf/'); assert.equal(opts.download, true); return blob;
  });
  assert.equal(result, blob);
  await assert.rejects(privatePdf(0, {}), /Invalid document ID/);
  await assert.rejects(privatePdf(1, {}, async () => new Blob([])), /empty/);
});
