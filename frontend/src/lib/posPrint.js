import { callMethod } from './api'

export const POS_THERMAL_PRINT_FORMAT = 'Rhocom POS Thermal Receipt'
export const POS_THERMAL_RAW_PRINT_FORMAT = 'Rhocom POS Thermal Raw Receipt'

let qzAssetsLoading = null

function loadScript(src) {
  return new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${src}"]`)
    if (existing) {
      existing.addEventListener('load', resolve, { once: true })
      existing.addEventListener('error', reject, { once: true })
      if (existing.dataset.loaded === '1') resolve()
      return
    }

    const script = document.createElement('script')
    script.src = src
    script.async = true
    script.onload = () => {
      script.dataset.loaded = '1'
      resolve()
    }
    script.onerror = () => reject(new Error(`Failed to load ${src}`))
    document.head.appendChild(script)
  })
}

async function ensureQZTray() {
  if (window.qz?.version) return window.qz

  if (!qzAssetsLoading) {
    qzAssetsLoading = Promise.all([
      loadScript('/assets/frappe/node_modules/js-sha256/build/sha256.min.js'),
      loadScript('/assets/frappe/node_modules/qz-tray/qz-tray.js'),
    ]).then(() => {
      const qz = window.qz
      if (!qz?.api) throw new Error('QZ Tray is not available')

      qz.api.setPromiseType((resolver) => new Promise(resolver))
      qz.api.setSha256Type((data) => window.sha256(data))
      return qz
    })
  }

  return qzAssetsLoading
}

async function connectQZ() {
  const qz = await ensureQZTray()
  if (qz.websocket.isActive()) return qz

  try {
    await qz.websocket.connect()
  } catch (error) {
    if (error?.message === 'Unable to establish connection with QZ') {
      window.location.assign('qz:launch')
      await qz.websocket.connect({ retries: 3, delay: 1 })
    } else {
      throw error
    }
  }

  return qz
}

function getMappedPrinterName() {
  const explicitPrinter = localStorage.getItem('pos_thermal_printer')
  if (explicitPrinter) return explicitPrinter

  try {
    const mapping = JSON.parse(localStorage.getItem('print_format_printer_map') || '{}')
    const invoiceMappings = mapping['POS Invoice'] || []
    const match = invoiceMappings.find((row) =>
      row.print_format === POS_THERMAL_RAW_PRINT_FORMAT || row.print_format === POS_THERMAL_PRINT_FORMAT
    )
    return match?.printer || ''
  } catch {
    return ''
  }
}

async function getPrinterName(qz) {
  const mappedPrinter = getMappedPrinterName()
  if (mappedPrinter) return mappedPrinter
  return qz.printers.getDefault()
}

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

export async function printPOSInvoiceDirect(invoiceName) {
  if (!invoiceName) throw new Error('Invoice name is required')

  const qz = await connectQZ()
  const printerName = await getPrinterName(qz)
  if (!printerName) throw new Error('No default printer found')

  const output = await callMethod('frappe.www.printview.get_rendered_raw_commands', {
    doc: 'POS Invoice',
    name: invoiceName,
    print_format: POS_THERMAL_RAW_PRINT_FORMAT,
  })

  const rawCommands = output?.raw_commands
  if (!rawCommands) throw new Error('No raw print output returned')

  const config = qz.configs.create(printerName)
  await qz.print(config, [rawCommands])

  return { printerName }
}

export async function printPOSInvoice(invoiceName, { fallbackToPreview = true } = {}) {
  try {
    return await printPOSInvoiceDirect(invoiceName)
  } catch (error) {
    console.warn('[POS Print] Direct print failed; falling back to browser print.', error)
    if (fallbackToPreview) {
      window.open(getPOSInvoicePrintUrl(invoiceName), '_blank')
    }
    return { fallback: true, error }
  }
}