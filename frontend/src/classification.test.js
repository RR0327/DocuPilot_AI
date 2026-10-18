import test from 'node:test';
import assert from 'node:assert/strict';
import { validClassification, classificationLabel } from './classification.js';
test('only recognized categories are accepted', () => {
 assert.equal(classificationLabel('invoice'), 'Invoice');
 assert.equal(classificationLabel('unknown'), 'Needs review');
 assert.equal(classificationLabel('made-up'), 'Not classified');
});
test('classification evidence requires a positive source page', () => {
 const result = {category:'contract', reason:'rule evidence', evidence:[{page_number:2,phrase:'governing law',excerpt:'governing law applies'}]};
 assert.equal(validClassification(result),true);
 assert.equal(validClassification({...result,evidence:[{...result.evidence[0],page_number:0}]}),false);
 assert.equal(validClassification({...result,category:'invalid'}),false);
});
