import test from 'node:test';
import assert from 'node:assert/strict';
import { currencySeries, supplierSeries } from './analytics.js';

test('monthly series excludes other currencies and orders months', () => {
  const data = {monthly_trends:[
    {currency:'BDT',month:'2026-08',invoice_total:'100.00'},
    {currency:'USD',month:'2026-07',invoice_total:'200.00'},
    {currency:'BDT',month:'2026-07',invoice_total:'25.00'}]};
  assert.deepEqual(currencySeries(data,'BDT'),[{month:'2026-07',amount:25},{month:'2026-08',amount:100}]);
});

test('invalid amounts and labels never enter chart', () => {
  assert.deepEqual(currencySeries({monthly_trends:[{currency:'BDT',month:'bad',invoice_total:'12'}]},'BDT'),[]);
  assert.deepEqual(supplierSeries({top_suppliers:[{currency:'BDT',supplier:'Good',invoice_total:'42.00'},
    {currency:'USD',supplier:'Other',invoice_total:'99'},
    {currency:'BDT',supplier:'Bad',invoice_total:'NaN'}]},'BDT'),[{supplier:'Good',amount:42}]);
});
