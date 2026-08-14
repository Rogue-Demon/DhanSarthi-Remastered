import React from 'react'
import { useProfile, useDashboardData, useTransactions, useGoals } from '@/hooks'
import { Badge, Button } from '@/components/ui'
import { motion, useReducedMotion } from 'framer-motion'
import { DashboardGrid, WidgetContainer, DashboardSection } from '@/components/dashboard'
import * as LucideIcons from 'lucide-react'

export function Overview() {
  const { profile } = useProfile()
  const shouldReduceMotion = useReducedMotion()

  // Load real financial and ledger data
  const { data: dashboardData, isLoading: dashLoading } = useDashboardData()
  const { data: txData, isLoading: txLoading } = useTransactions({ page: 1, page_size: 4 })
  const { data: goalsData, isLoading: goalsLoading } = useGoals()

  if (dashLoading || txLoading || goalsLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full">
        <div className="col-span-3 h-28 bg-muted/20 animate-pulse rounded-2xl border" />
        <div className="col-span-1 h-48 bg-muted/20 animate-pulse rounded-2xl border" />
        <div className="col-span-2 h-48 bg-muted/20 animate-pulse rounded-2xl border" />
        <div className="col-span-3 h-32 bg-muted/20 animate-pulse rounded-2xl border" />
      </div>
    )
  }

  // Fallback structures if no data is present
  const summary = dashboardData?.summary || { total_income: 0, total_expenses: 0, savings: 0 }
  const netFlow = dashboardData?.cash_flow?.net_cash_flow || 0

  // Calculate health score dynamically
  const totalAssets = parseFloat(dashboardData?.net_worth?.total_assets || 0)
  const totalLiabilities = parseFloat(dashboardData?.net_worth?.total_liabilities || 0)
  const dti = parseFloat(dashboardData?.financial_health?.dti_percent || 0)
  const savingsRate = parseFloat(dashboardData?.financial_health?.savings_rate_percent || 0)

  const healthScore = dashboardData
    ? Math.round(
        (savingsRate > 0 ? Math.min(savingsRate * 2.5, 40) : 15) +
          (dti > 0 ? Math.max(0, 40 - dti) : 30) +
          (totalAssets > 0 ? Math.min((totalAssets / Math.max(1, totalLiabilities)) * 5, 20) : 10)
      )
    : 80

  const activities = (txData?.items || []).map((tx) => {
    const isIncome = tx.transaction_type === 'INCOME'
    return {
      text: tx.description || tx.category,
      value: `${isIncome ? '+' : '-'}₹${parseFloat(tx.amount).toLocaleString('en-IN')}`,
      date: new Date(tx.transaction_date).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      }),
      icon: isIncome ? 'ArrowUpRight' : 'ArrowDownLeft',
      color: isIncome ? '#10B981' : '#EF4444',
    }
  })

  const goals = goalsData?.items || []

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 w-full text-left"
    >
      <DashboardGrid>
        {/* Core Financial Summary Metric Row */}
        <div className="lg:col-span-12 grid grid-cols-1 sm:grid-cols-3 gap-6 bg-muted/20 border border-border/80 p-5 rounded-2xl">
          <div className="flex flex-col text-left pl-3 border-l-3 border-primary">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Inflows (Income)
            </span>
            <span className="text-2xl font-extrabold text-text-primary tracking-tight mt-2.5">
              ₹{parseFloat(summary.total_income).toLocaleString('en-IN')}
            </span>
          </div>
          <div className="flex flex-col text-left border-x border-border/80 px-6 pl-6 border-l-3 border-danger/80">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Outflows (Expenses)
            </span>
            <span className="text-2xl font-extrabold text-text-primary tracking-tight mt-2.5">
              ₹{parseFloat(summary.total_expenses).toLocaleString('en-IN')}
            </span>
          </div>
          <div className="flex flex-col text-left pl-6 border-l-3 border-success/80">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Net Surplus (Flow)
            </span>
            <span className="text-2xl font-extrabold text-text-primary tracking-tight mt-2.5">
              ₹{parseFloat(netFlow).toLocaleString('en-IN')}
            </span>
          </div>
        </div>

        {/* Column 1: Financial Health Indicator */}
        <WidgetContainer
          title="Financial Health Score"
          icon="Activity"
          sizeClass="lg:col-span-4 md:col-span-1"
        >
          <div className="flex flex-col items-center justify-center text-center gap-4 py-2">
            <div className="relative h-20 w-20 flex items-center justify-center">
              <svg className="h-full w-full transform -rotate-90" viewBox="0 0 36 36">
                <path
                  className="text-muted"
                  strokeWidth="3"
                  stroke="currentColor"
                  fill="transparent"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
                <path
                  className="text-primary"
                  strokeWidth="3"
                  strokeDasharray={`${healthScore}, 100`}
                  strokeLinecap="round"
                  stroke="currentColor"
                  fill="transparent"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
              </svg>
              <span className="absolute text-base font-black text-text-primary">
                {healthScore}%
              </span>
            </div>
            <div className="flex flex-col gap-1">
              <Badge
                variant="secondary"
                className="mx-auto text-[9px] font-bold bg-primary/10 text-primary border-primary/20 py-0.5 px-2 rounded"
              >
                {healthScore >= 75
                  ? 'Strong Health'
                  : healthScore >= 50
                    ? 'Stable Health'
                    : 'Review Health'}
              </Badge>
              <p className="text-[10px] font-bold text-text-muted leading-relaxed max-w-[180px] mt-1.5">
                {healthScore >= 75
                  ? 'Excellent savings and assets leverage ratios.'
                  : 'Consider capping discretionary expense flows.'}
              </p>
            </div>
          </div>
        </WidgetContainer>

        {/* Column 2: Recent Activity Timeline */}
        <WidgetContainer
          title="Ledger Timeline"
          icon="History"
          sizeClass="lg:col-span-8 md:col-span-2"
        >
          <div className="flex flex-col gap-4 py-1 text-left">
            {activities.length > 0 ? (
              <div className="flex flex-col gap-3.5 border-l border-border/80 ml-2 pl-4 relative">
                {activities.map((act, idx) => {
                  const Icon = LucideIcons[act.icon] || LucideIcons.Info
                  return (
                    <div
                      key={idx}
                      className="flex justify-between items-center text-xs relative group"
                    >
                      <div className="absolute left-[-21.5px] top-[4px] h-3.5 w-3.5 rounded-full border-2 border-card bg-primary flex items-center justify-center text-white">
                        <Icon className="h-1.5 w-1.5 stroke-[2.5]" />
                      </div>
                      <div className="flex flex-col gap-0.5">
                        <span className="font-extrabold text-text-primary group-hover:text-primary transition-colors duration-200 capitalize">
                          {act.text.replace(/_/g, ' ').toLowerCase()}
                        </span>
                        <span className="text-[9px] font-bold text-text-muted">{act.date}</span>
                      </div>
                      <span className="font-black text-text-secondary">{act.value}</span>
                    </div>
                  )
                })}
              </div>
            ) : (
              <span className="text-xs font-bold text-text-muted py-8 text-center block">
                No recent transactions recorded.
              </span>
            )}
          </div>
        </WidgetContainer>

        {/* Goal summary list */}
        <WidgetContainer
          title="Active Goal Target Summary"
          icon="Target"
          sizeClass="lg:col-span-12"
        >
          {goals.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 py-2">
              {goals.map((goal) => {
                const pct =
                  Math.round(
                    (parseFloat(goal.current_amount) / parseFloat(goal.target_amount)) * 100
                  ) || 0
                return (
                  <div
                    key={goal.id}
                    className="flex items-center gap-4 bg-muted/30 border border-border p-3.5 rounded-xl text-left select-none relative group hover:border-primary/20 transition-all duration-200"
                  >
                    <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0 border">
                      <LucideIcons.Compass className="h-5 w-5" />
                    </div>
                    <div className="flex-1 flex flex-col gap-1">
                      <div className="flex justify-between text-xs font-black text-text-primary leading-none">
                        <span>{goal.name}</span>
                        <span>{pct}%</span>
                      </div>
                      <div className="w-full bg-muted h-2 rounded-full mt-1.5 overflow-hidden border border-white/60">
                        <div
                          className="h-full rounded-full transition-all duration-500 bg-primary"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <div className="flex justify-between items-center text-[9px] font-bold text-text-muted mt-1 uppercase tracking-wider">
                        <span>
                          Saved: ₹{parseFloat(goal.current_amount).toLocaleString('en-IN')}
                        </span>
                        <span>
                          Target: ₹{parseFloat(goal.target_amount).toLocaleString('en-IN')}
                        </span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <span className="text-xs font-bold text-text-muted py-8 text-center block">
              No active goals configured yet.
            </span>
          )}
        </WidgetContainer>
      </DashboardGrid>
    </motion.div>
  )
}

export default Overview
