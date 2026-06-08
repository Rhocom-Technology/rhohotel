export const POS_THERMAL_PRINT_FORMAT = 'Rhocom POS Thermal Receipt'

export function getPOSInvoicePrintUrl(invoiceName, { triggerPrint = true } = {}) {
  const params = new URLSearchParams({
    doctype: 'POS Invoice',
    name: invoiceName,
    format: POS_THERMAL_PRINT_FORMAT,
    no_letterhead: '1',
  })

  if (triggerPrint) {
    params.set('trigger_print', '1')
  }

  return `/printview?${params.toString()}`
}