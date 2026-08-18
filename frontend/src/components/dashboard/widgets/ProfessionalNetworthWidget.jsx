import React from 'react'
import { Badge } from '@/components/ui'
import * as LucideIcons from 'lucide-react'
import { motion, useReducedMotion } from 'framer-motion'
import WidgetContainer from '../WidgetContainer'
import WidgetActions from '../WidgetActions'

export function ProfessionalNetworthWidget({ widget, sizeClass, dashboardData }) {
  const shouldReduceMotion = useReducedMotion()

  const netWorth = parseFloat(dashboardData?.net_worth?.net_worth || 0)
  const totalAssets = parseFloat(dashboardData?.net_worth?.total_assets || 0)
  const totalLiabilities = parseFloat(dashboardData?.net_worth?.total_liabilities || 0)

  // Derive a dynamic health score based on real backend metrics
  const dti = parseFloat(dashboardData?.financial_health?.dti_percent || 0)
  const savingsRate = parseFloat(dashboardData?.financial_health?.savings_rate_percent || 0)
  const healthScore = dashboardData
    ? Math.round(
        (savingsRate > 0 ? Math.min(savingsRate * 2.5, 40) : 15) +
          (dti > 0 ? Math.max(0, 40 - dti) : 30) +
          (totalAssets > 0 ? Math.min((totalAssets / Math.max(1, totalLiabilities)) * 5, 20) : 10)
      )
    : 78

  const toolbar = (
    <WidgetActions
      onInfo={() => alert('Net Worth calculation and financial health score')}
      onRefresh={() => console.log('Networth refresh')}
    />
  )

  return (
    <WidgetContainer
      title={widget.title}
      icon={widget.icon}
      color={widget.color}
      sizeClass={sizeClass}
      toolbar={toolbar}
    >
      <div className="flex flex-col gap-5 h-full select-none text-left font-sans">
        {/* Core Metric */}
        <div className="flex justify-between items-start">
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Estimated Net Worth
            </span>
            <span className="text-3xl font-extrabold text-text-primary tracking-tight mt-1.5">
              ₹{netWorth.toLocaleString('en-IN')}
            </span>
            <span className="text-xs text-text-secondary mt-1 font-medium flex items-center gap-1">
              <LucideIcons.ArrowUpRight className="h-3.5 w-3.5 text-success" />
              <span>Assets minus liabilities</span>
            </span>
          </div>
          <Badge
            variant="secondary"
            className="text-[10px] font-bold bg-success/10 border-success/15 text-success py-0.5 px-2 rounded"
          >
            {netWorth >= 0 ? 'Positive' : 'Deficit'}
          </Badge>
        </div>

        {/* Assets vs Liabilities Breakdown */}
        <div className="grid grid-cols-2 gap-4 bg-muted/30 border border-border/80 p-3 rounded-xl text-xs">
          <div className="flex flex-col text-left pl-2 border-l-2 border-success">
            <span className="font-bold text-text-muted">Total Assets</span>
            <span className="text-sm font-extrabold text-text-primary mt-1">
              ₹{totalAssets.toLocaleString('en-IN')}
            </span>
          </div>
          <div className="flex flex-col text-left pl-2 border-l-2 border-danger">
            <span className="font-bold text-text-muted">Total Liabilities</span>
            <span className="text-sm font-extrabold text-text-primary mt-1">
              ₹{totalLiabilities.toLocaleString('en-IN')}
            </span>
          </div>
        </div>

        {/* Financial Health Score (Executive look) */}
        <div className="flex items-center gap-4 mt-auto border-t border-border/40 pt-4">
          {/* Minimal health score progress ring */}
          <div className="relative h-12 w-12 flex items-center justify-center shrink-0">
            <svg className="h-full w-full transform -rotate-90" viewBox="0 0 36 36">
              <path
                className="text-muted"
                strokeWidth="3"
                stroke="currentColor"
                fill="transparent"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                className="text-primary transition-all duration-500"
                strokeWidth="3"
                strokeDasharray={`${healthScore}, 100`}
                strokeLinecap="round"
                stroke="currentColor"
                fill="transparent"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>
            <span className="absolute text-[10px] font-black text-text-primary">
              {healthScore}%
            </span>
          </div>

          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-extrabold text-text-primary">
                Financial Health Score
              </span>
              <Badge
                variant="secondary"
                className="text-[8px] font-bold py-0 px-1 bg-primary/10 border-primary/20 text-primary"
              >
                {healthScore >= 75 ? 'Strong' : healthScore >= 50 ? 'Stable' : 'Review'}
              </Badge>
            </div>
            <span className="text-[10px] font-bold text-text-muted mt-0.5 leading-tight">
              {healthScore >= 75
                ? 'Excellent debt-to-income and savings margin.'
                : 'Optimize budget utilization and goals.'}
            </span>
          </div>
        </div>
      </div>
    </WidgetContainer>
  )
}

export default ProfessionalNetworthWidget
