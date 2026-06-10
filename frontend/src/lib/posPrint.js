import { callMethod } from './api'

export const POS_THERMAL_PRINT_FORMAT = 'Rhocom POS Thermal Receipt'
export const POS_THERMAL_RAW_PRINT_FORMAT = 'Rhocom POS Thermal Raw Receipt'
export const POS_DIRECT_PRINT_TIMEOUT_MS = 5000

let qzAssetsLoading = null
let reservedPreviewWindow = null

function directPrintTimeout(timeoutMs) {
  return new Promise((_, reject) => {
    window.setTimeout(() => reject(new Error(`Direct POS print timed out after ${timeoutMs}ms`)), timeoutMs)
  })
}

function assertDirectPrintActive(session) {
  if (session && !session.active) throw new Error('Direct POS print timed out')
}

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
  return getPrintViewUrl('POS Invoice', invoiceName, POS_THERMAL_PRINT_FORMAT, { triggerPrint })
}

export function getPrintViewUrl(doctype, name, printFormat = null, { triggerPrint = true } = {}) {
  const params = new URLSearchParams({
    doctype,
    name,
    no_letterhead: '1',
  })

  if (printFormat) params.set('format', printFormat)

  if (triggerPrint) {
    params.set('trigger_print', '1')
  }

  return `/printview?${params.toString()}`
}

export function reservePOSInvoicePrintPreview() {
  if (reservedPreviewWindow && !reservedPreviewWindow.closed) return reservedPreviewWindow
  try {
    reservedPreviewWindow = window.open('', '_blank')
    if (reservedPreviewWindow) {
      reservedPreviewWindow.document.write('<!doctype html><title>Preparing receipt...</title><body style="font-family:sans-serif;padding:24px;color:#475569;">Preparing receipt...</body>')
      reservedPreviewWindow.document.close()
    }
  } catch (_) {
    reservedPreviewWindow = null
  }
  return reservedPreviewWindow
}

export function clearReservedPOSInvoicePrintPreview() {
  if (reservedPreviewWindow && !reservedPreviewWindow.closed) {
    reservedPreviewWindow.close()
  }
  reservedPreviewWindow = null
}

export function openReservedPrintPreview(doctype, name, printFormat = null) {
  if (!doctype || !name) return false
  const url = getPrintViewUrl(doctype, name, printFormat)
  if (reservedPreviewWindow && !reservedPreviewWindow.closed) {
    reservedPreviewWindow.location.href = url
  } else {
    const opened = window.open(url, '_blank')
    if (!opened) window.location.href = url
  }
  reservedPreviewWindow = null
  return true
}

export async function printPOSInvoiceDirect(invoiceName, { session = null } = {}) {
  if (!invoiceName) throw new Error('Invoice name is required')

  assertDirectPrintActive(session)
  const qz = await connectQZ()
  assertDirectPrintActive(session)
  const printerName = await getPrinterName(qz)
  if (!printerName) throw new Error('No default printer found')
  assertDirectPrintActive(session)

  const output = await callMethod('frappe.www.printview.get_rendered_raw_commands', {
    doc: 'POS Invoice',
    name: invoiceName,
    print_format: POS_THERMAL_RAW_PRINT_FORMAT,
  })
  assertDirectPrintActive(session)

  const rawCommands = output?.raw_commands
  if (!rawCommands) throw new Error('No raw print output returned')

  const config = qz.configs.create(printerName)
  assertDirectPrintActive(session)
  await qz.print(config, [rawCommands])
  assertDirectPrintActive(session)

  return { printerName }
}

export async function printPOSInvoice(invoiceName, { fallbackToPreview = true, directTimeoutMs = POS_DIRECT_PRINT_TIMEOUT_MS } = {}) {
  const session = { active: true }
  try {
    const result = await Promise.race([
      printPOSInvoiceDirect(invoiceName, { session }),
      directPrintTimeout(directTimeoutMs),
    ])
    session.active = false
    if (reservedPreviewWindow && !reservedPreviewWindow.closed) {
      reservedPreviewWindow.close()
    }
    reservedPreviewWindow = null
    return result
  } catch (error) {
    session.active = false
    console.warn('[POS Print] Direct print failed; falling back to browser print.', error)
    if (fallbackToPreview) {
      const url = getPOSInvoicePrintUrl(invoiceName)
      if (reservedPreviewWindow && !reservedPreviewWindow.closed) {
        reservedPreviewWindow.location.href = url
      } else {
        const opened = window.open(url, '_blank')
        if (!opened) window.location.href = url
      }
    }
    reservedPreviewWindow = null
    return { fallback: true, error }
  }
}