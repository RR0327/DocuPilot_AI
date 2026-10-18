/** Present money per explicit currency; never combine FX-denominated amounts. */
export function currencySeries(payload, currency) {
  if (!payload || !Array.isArray(payload.monthly_trends)) return [];
  return payload.monthly_trends
    .filter(row => row.currency === currency && /^\d{4}-(0[1-9]|1[0-2])$/.test(row.month))
    .map(row => ({ month: row.month, amount: Number(row.invoice_total) }))
    .filter(row => Number.isFinite(row.amount) && row.amount >= 0)
    .sort((a, b) => a.month.localeCompare(b.month));
}

export function supplierSeries(payload, currency) {
  if (!payload || !Array.isArray(payload.top_suppliers)) return [];
  return payload.top_suppliers
    .filter(row => row.currency === currency && typeof row.supplier === 'string')
    .map(row => ({ supplier: row.supplier, amount: Number(row.invoice_total) }))
    .filter(row => Number.isFinite(row.amount) && row.amount >= 0);
}
