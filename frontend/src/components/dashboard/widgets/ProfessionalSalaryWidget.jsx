import { Badge, Button } from '@/components/ui'
import * as LucideIcons from 'lucide-react'
import { motion, useReducedMotion } from 'framer-motion'
import { cn } from '@/utils'
import WidgetContainer from '../WidgetContainer'
import WidgetActions from '../WidgetActions'

export function ProfessionalSalaryWidget({ widget, sizeClass, dashboardData }) {
  const shouldReduceMotion = useReducedMotion()
  const totalIncome = parseFloat(dashboardData?.summary?.total_income || 0)
  const categories = Object.entries(dashboardData?.cash_flow?.income_by_category || {})

  const toolbar = (
    <WidgetActions
      onInfo={() => alert('Salary and income streams overview')}
      onRefresh={() => console.log('Salary refresh')}
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
              Primary Income Streams
            </span>
            <span className="text-3xl font-extrabold text-text-primary tracking-tight mt-1.5">
              ₹{totalIncome.toLocaleString('en-IN')}
            </span>
            <span className="text-xs text-text-secondary mt-1 font-medium flex items-center gap-1">
              <LucideIcons.CheckCircle className="h-3.5 w-3.5 text-success" />
              <span>Base salary and inflow credits</span>
            </span>
          </div>
          <Badge
            variant="secondary"
            className="text-[10px] font-bold bg-success/10 border-success/15 text-success py-0.5 px-2 rounded"
          >
            {totalIncome > 0 ? 'Active' : 'No Data'}
          </Badge>
        </div>

        {/* Breakdown details */}
        <div className="flex flex-col gap-2.5 bg-muted/30 border border-border/80 p-3.5 rounded-xl text-xs font-semibold text-text-secondary">
          {categories.length > 0 ? (
            categories.map(([cat, val], idx) => (
              <div
                key={cat}
                className={cn('flex justify-between', idx > 0 && 'border-t border-border/40 pt-2')}
              >
                <span className="capitalize">{cat.replace(/_/g, ' ').toLowerCase()}</span>
                <span className="font-bold text-text-primary">
                  ₹{parseFloat(val).toLocaleString('en-IN')}
                </span>
              </div>
            ))
          ) : (
            <div className="text-center py-2 text-text-muted">
              No income records configured yet.
            </div>
          )}
        </div>

        {/* Micro-Chart Placeholder: Income vs Expense Trend */}
        <div className="flex flex-col gap-2 mt-auto border-t border-border/40 pt-4">
          <div className="flex justify-between items-center text-[10px] font-bold text-text-muted uppercase tracking-wider">
            <span>Income vs Expense Margin</span>
            <span>Last 3 months</span>
          </div>

          <div className="h-16 w-full rounded-xl bg-card border border-border/70 relative flex items-end justify-around px-4 pb-2.5 overflow-hidden">
            <div className="absolute inset-0 opacity-[0.02] bg-[radial-gradient(#7C3AED_1px,transparent_1px)] [background-size:10px_10px]" />

            {/* Simple executive bar comparisons */}
            {[45, 60, 75].map((val, idx) => (
              <div key={idx} className="flex items-end gap-1 h-full">
                {/* Income bar */}
                <div className="w-2 rounded bg-primary" style={{ height: `${val}%` }} />
                {/* Expense bar */}
                <div className="w-2 rounded bg-primary/20" style={{ height: `${val * 0.45}%` }} />
              </div>
            ))}

            {/* Legend inside chart */}
            <div className="absolute top-1.5 right-2 flex gap-2 text-[8px] font-bold text-text-muted">
              <div className="flex items-center gap-1">
                <div className="h-1.5 w-1.5 rounded-full bg-primary" />
                <span>In</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="h-1.5 w-1.5 rounded-full bg-primary/20" />
                <span>Out</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </WidgetContainer>
  )
}

export default ProfessionalSalaryWidget
