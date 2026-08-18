import React, { useState } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { Button, Badge } from '@/components/ui'
import * as LucideIcons from 'lucide-react'
import { downloadReport } from '@/services/api/reports'

export function Export() {
  const shouldReduceMotion = useReducedMotion()
  const [selectedReportType, setSelectedReportType] = useState('monthly_executive')
  const [exportingFormat, setExportingFormat] = useState(null)
  const [errorMessage, setErrorMessage] = useState('')

  const reportTypes = [
    {
      id: 'monthly_executive',
      name: 'Monthly Executive Statement',
      desc: 'High-level financial summary including Net Worth, Cash Flow, Assets, and Debt KPIs',
      badge: 'Popular',
    },
    {
      id: 'annual_tax_summary',
      name: 'Annual Financial & Tax Summary',
      desc: 'Comprehensive yearly financial statement for auditing, tax filing, and records',
      badge: 'Annual',
    },
    {
      id: 'expense_breakdown',
      name: 'Expense & Cash Flow Ledger',
      desc: 'Detailed record of inflows, category-wise outflows, and net periodic surplus',
      badge: 'Detailed',
    },
    {
      id: 'net_worth_statement',
      name: 'Net Worth & Asset Schedule',
      desc: 'Full breakdown of current assets, real estate, liquid funds, and liabilities',
      badge: 'Balance Sheet',
    },
    {
      id: 'goal_feasibility',
      name: 'Financial Goals Progress',
      desc: 'Status of active targets, target dates, current savings, and funding gaps',
      badge: 'Milestones',
    },
    {
      id: 'debt_snowball',
      name: 'Liabilities & Loan Amortization',
      desc: 'Schedule of outstanding loans, interest rates, DTI ratio, and debt obligations',
      badge: 'Liabilities',
    },
  ]

  const exportFormats = [
    {
      id: 'pdf',
      format: 'PDF Document (.pdf)',
      desc: 'Formatted executive statement with DhanSarthi branding & styled table layouts',
      icon: 'FileText',
      color: '#EF4444',
    },
    {
      id: 'xlsx',
      format: 'Excel Workbook (.xlsx)',
      desc: 'Multi-column spreadsheet with header fills, borders, and auto-adjusted widths',
      icon: 'Table',
      color: '#10B981',
    },
    {
      id: 'csv',
      format: 'CSV Data Ledger (.csv)',
      desc: 'UTF-8 encoded standard CSV export compatible with Tally, Excel, and accounting tools',
      icon: 'FileCode',
      color: '#3B82F6',
    },
    {
      id: 'print',
      format: 'Print Statement',
      desc: 'High-contrast clean layout formatted directly for browser paper printing',
      icon: 'Printer',
      color: '#7C3AED',
    },
  ]

  const handleExport = async (formatId) => {
    if (formatId === 'print') {
      window.print()
      return
    }

    try {
      setErrorMessage('')
      setExportingFormat(formatId)
      await downloadReport({
        reportType: selectedReportType,
        format: formatId,
      })
    } catch (err) {
      console.error('Failed to export report:', err)
      setErrorMessage(err.message || 'Export failed. Please check backend connection.')
    } finally {
      setExportingFormat(null)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-8 w-full text-left select-none max-w-5xl mx-auto pb-12"
    >
      {/* Header */}
      <div className="flex flex-col gap-1.5 border-b border-border/40 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-2xl bg-primary/10 text-primary border border-primary/20">
            <LucideIcons.FileDown className="h-6 w-6 stroke-[2.2]" />
          </div>
          <div>
            <h3 className="text-xl font-black text-text-primary uppercase tracking-wider leading-tight">
              Financial Report Export Center
            </h3>
            <p className="text-xs font-bold text-text-muted">
              Generate live, authoritative financial statements directly from your DhanSarthi engine
              data.
            </p>
          </div>
        </div>
      </div>

      {errorMessage && (
        <div className="p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-xs font-bold flex items-center gap-2">
          <LucideIcons.AlertCircle className="h-4 w-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Step 1: Select Report Type */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-2">
          <span className="flex items-center justify-center h-6 w-6 rounded-full bg-primary text-white text-xs font-black">
            1
          </span>
          <h4 className="text-sm font-black text-text-primary uppercase tracking-wider">
            Select Statement Type
          </h4>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {reportTypes.map((type) => {
            const isSelected = selectedReportType === type.id

            return (
              <div
                key={type.id}
                onClick={() => setSelectedReportType(type.id)}
                className={`cursor-pointer p-4 rounded-2xl border transition-all flex flex-col justify-between gap-3 text-left relative overflow-hidden ${
                  isSelected
                    ? 'clay-surface bg-primary/5 border-primary shadow-md ring-2 ring-primary/20'
                    : 'bg-card border-border hover:border-primary/40 hover:bg-primary/5'
                }`}
              >
                <div className="flex flex-col gap-1">
                  <div className="flex items-center justify-between gap-2">
                    <span
                      className={`text-xs font-black ${isSelected ? 'text-primary' : 'text-text-primary'}`}
                    >
                      {type.name}
                    </span>
                    <Badge
                      variant={isSelected ? 'default' : 'secondary'}
                      className="text-[10px] py-0 px-2 font-bold"
                    >
                      {type.badge}
                    </Badge>
                  </div>
                  <p className="text-[11px] font-medium text-text-muted leading-relaxed">
                    {type.desc}
                  </p>
                </div>

                <div className="flex items-center gap-1.5 text-[11px] font-bold text-primary">
                  <LucideIcons.CheckCircle2
                    className={`h-4 w-4 transition-transform ${isSelected ? 'scale-100' : 'opacity-0 scale-75'}`}
                  />
                  <span>{isSelected ? 'Selected' : 'Select'}</span>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Step 2: Select Format & Download */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-2">
          <span className="flex items-center justify-center h-6 w-6 rounded-full bg-primary text-white text-xs font-black">
            2
          </span>
          <h4 className="text-sm font-black text-text-primary uppercase tracking-wider">
            Choose Export Format & Download
          </h4>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {exportFormats.map((fmt) => {
            const Icon = LucideIcons[fmt.icon] || LucideIcons.Download
            const isExporting = exportingFormat === fmt.id

            return (
              <div
                key={fmt.id}
                className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl shadow-card flex flex-col justify-between gap-4 text-left group hover:border-primary/30 transition-all"
              >
                <div className="flex flex-col gap-3">
                  <div
                    className="p-3 rounded-xl flex items-center justify-center shrink-0 border shadow-xs w-fit"
                    style={{
                      background: `${fmt.color}15`,
                      color: fmt.color,
                      borderColor: `${fmt.color}30`,
                    }}
                  >
                    <Icon className="h-6 w-6 stroke-[2.2]" />
                  </div>

                  <div className="flex flex-col gap-1">
                    <span className="text-xs font-black text-text-primary group-hover:text-primary transition-colors">
                      {fmt.format}
                    </span>
                    <span className="text-[10px] font-medium text-text-muted leading-relaxed">
                      {fmt.desc}
                    </span>
                  </div>
                </div>

                <Button
                  variant={fmt.id === 'pdf' ? 'default' : 'secondary'}
                  size="sm"
                  disabled={isExporting}
                  className="w-full rounded-xl font-bold text-xs justify-center shadow-xs"
                  onClick={() => handleExport(fmt.id)}
                  iconLeft={
                    isExporting ? (
                      <LucideIcons.Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <LucideIcons.Download className="h-3.5 w-3.5" />
                    )
                  }
                >
                  {isExporting ? 'Generating...' : `Export ${fmt.id.toUpperCase()}`}
                </Button>
              </div>
            )
          })}
        </div>
      </div>
    </motion.div>
  )
}

export default Export
