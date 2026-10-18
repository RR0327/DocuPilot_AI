import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
const component = readFileSync(fileURLToPath(new URL('./ReviewQueue.jsx', import.meta.url)), 'utf8');
const app = readFileSync(fileURLToPath(new URL('./App.jsx', import.meta.url)), 'utf8');
test('review screen exposes queue and owner review endpoints', () => {
  assert.match(component, /\/reviews\/\?status=/);
  assert.match(component, /\/reviews\/\$\{id\}\//);
  assert.match(app, /Human review/);
});
test('review controls offer approve, reject, reopen and source excerpts', () => {
  for (const action of ['approve', 'reject', 'reopen']) assert.ok(component.includes(action));
  assert.match(component, /source_references/);
  assert.match(component, /Review history/);
});
