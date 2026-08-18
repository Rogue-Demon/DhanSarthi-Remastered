import React from 'react'
import { useProfile } from '@/hooks'
import { PROFILES } from '@/constants'
import * as LucideIcons from 'lucide-react'
import { cn } from '@/utils'

/**
 * DashboardSummary Component
 *
 * Renders a row of metric placeholder cards (summary strip) representing key
 * financial indicators customized for the active profile.
 */
export function DashboardSummary({ className, dashboardData, ...props }) {
  const { profile, profileConfig } = useProfile()

  if (!profileConfig) return null

  // Resolved real data structures depending on profile context
  const getSummaryMetrics = () => {
    const summary = dashboardData?.summary || {
      total_income: 0,
      total_expenses: 0,
      savings: 0,
      net_worth: 0,
      total_assets: 0,
      total_liabilities: 0,
      total_invested: 0,
      total_debt: 0,
    }
    const cashFlow = dashboardData?.cash_flow || { net_cash_flow: 0 }
    const goals = dashboardData?.goals || { active_count: 0 }

    const formatCurrency = (val) => {
      return '₹' + parseFloat(val || 0).toLocaleString('en-IN')
    }

    switch (profile) {
      case PROFILES.STUDENT:
        return [
          {
            label: 'Monthly Allowance',
            value: formatCurrency(summary.total_income),
            icon: 'Wallet',
            trend: 'Active income inflow',
            color: '#8B5CF6',
          },
          {
            label: 'Savings Balance',
            value: formatCurrency(summary.savings),
            icon: 'PiggyBank',
            trend: 'Accumulated savings',
            color: '#EC4899',
          },
          {
            label: 'Monthly Expenditures',
            value: formatCurrency(summary.total_expenses),
            icon: 'TrendingDown',
            trend: 'Outflow spending',
            color: '#EF4444',
          },
          {
            label: 'Active Goals',
            value: `${goals.active_count} Targets`,
            icon: 'Target',
            trend: 'Goals in progress',
            color: '#F59E0B',
          },
        ]
      case PROFILES.PROFESSIONAL:
        return [
          {
            label: 'Net Monthly Income',
            value: formatCurrency(summary.total_income),
            icon: 'Briefcase',
            trend: 'Income inflow logs',
            color: '#7C3AED',
          },
          {
            label: 'Accumulated Assets',
            value: formatCurrency(summary.total_assets),
            icon: 'Gem',
            trend: 'Total stored assets',
            color: '#10B981',
          },
          {
            label: 'Active Liabilities',
            value: formatCurrency(summary.total_liabilities),
            icon: 'Handshake',
            trend: 'Total debt balance',
            color: '#EF4444',
          },
          {
            label: 'Current Net Worth',
            value: formatCurrency(summary.net_worth),
            icon: 'Coins',
            trend: 'Assets minus liabilities',
            color: '#F59E0B',
          },
        ]
      case PROFILES.BUSINESS:
        return [
          {
            label: 'Gross Monthly Revenue',
            value: formatCurrency(summary.total_income),
            icon: 'IndianRupee',
            trend: 'Total invoice cash inflows',
            color: '#4F46E5',
          },
          {
            label: 'Estimated Profit Margin',
            value: formatCurrency(summary.savings),
            icon: 'Sparkles',
            trend: 'Operating margin surplus',
            color: '#10B981',
          },
          {
            label: 'Operational Cost (OPEX)',
            value: formatCurrency(summary.total_expenses),
            icon: 'TrendingDown',
            trend: 'Overheads & business payments',
            color: '#EF4444',
          },
          {
            label: 'Liquidity Cash Flow',
            value: formatCurrency(cashFlow.net_cash_flow),
            icon: 'RefreshCw',
            trend: 'Net cash flow yield',
            color: '#0EA5E9',
          },
        ]
      default:
        return []
    }
  }

  const metrics = getSummaryMetrics()

  return (
    <div
      className={cn('grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 w-full', className)}
      {...props}
    >
      {metrics.map((metric, idx) => {
        const IconComponent = LucideIcons[metric.icon] || LucideIcons.Layers

        return (
          <div
            key={idx}
            className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 shadow-card flex items-center justify-between gap-4 select-none relative group overflow-hidden"
          >
            {/* Soft decorative background highlight bar */}
            <div
              className="absolute left-0 top-0 bottom-0 w-1 transition-all duration-300 group-hover:w-1.5"
              style={{ background: metric.color }}
            />

            <div className="flex flex-col gap-1.5 text-left pl-1">
              <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                {metric.label}
              </span>
              <span className="text-2xl font-black text-text-primary tracking-tight leading-none">
                {metric.value}
              </span>
              <span className="text-[10px] font-bold text-text-secondary">{metric.trend}</span>
            </div>

            {/* Icon Container with clay-like depth */}
            <div
              className="p-3.5 rounded-2xl flex items-center justify-center border border-white/40 dark:border-white/5 shadow-xs shrink-0"
              style={{
                background: `${metric.color}10`,
                color: metric.color,
              }}
            >
              <IconComponent className="h-5 w-5 stroke-[2px]" />
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default DashboardSummary
