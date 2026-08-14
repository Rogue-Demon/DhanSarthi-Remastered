import { envConfig } from '@/config'
import { requestInterceptor } from './interceptors'
import { ENDPOINTS } from './endpoints'

/**
 * Downloads a formatted financial report from the backend.
 *
 * @param {Object} params
 * @param {string} params.reportType - monthly_executive, annual_tax_summary, expense_breakdown, net_worth_statement, goal_feasibility, debt_snowball
 * @param {string} params.format - pdf, xlsx, csv
 * @param {string} [params.dateFrom] - YYYY-MM-DD
 * @param {string} [params.dateTo] - YYYY-MM-DD
 */
export async function downloadReport({
  reportType = 'monthly_executive',
  format = 'pdf',
  dateFrom,
  dateTo,
}) {
  const queryParams = new URLSearchParams({
    report_type: reportType,
    format: format,
  })

  if (dateFrom) queryParams.append('date_from', dateFrom)
  if (dateTo) queryParams.append('date_to', dateTo)

  const url = `${envConfig.apiBaseUrl}${ENDPOINTS.reports.export}?${queryParams.toString()}`
  const options = requestInterceptor({ method: 'GET' })

  const response = await fetch(url, options)

  if (!response.ok) {
    throw new Error(`Failed to export report: ${response.statusText}`)
  }

  // Extract filename from Content-Disposition header if present
  let filename = `dhansarthi_${reportType}.${format}`
  const disposition = response.headers.get('Content-Disposition')
  if (disposition && disposition.includes('filename=')) {
    const match = disposition.match(/filename="?([^"]+)"?/)
    if (match && match[1]) {
      filename = match[1]
    }
  }

  const blob = await response.blob()
  const downloadUrl = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = downloadUrl
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(downloadUrl)
}
