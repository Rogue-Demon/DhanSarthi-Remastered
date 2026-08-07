import React from 'react';
import { useProfile } from '@/hooks';
import { getFinanceConfig } from '@/config';
import { motion, useReducedMotion } from 'framer-motion';
import { DashboardGrid, WidgetContainer } from '@/components/dashboard';
import * as LucideIcons from 'lucide-react';
import { Badge } from '@/components/ui';

export function Expenses() {
  const { profile } = useProfile();
  const shouldReduceMotion = useReducedMotion();
  const financeData = getFinanceConfig(profile);

  if (!financeData) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 w-full text-left"
    >
      <div className="flex flex-col gap-2">
        <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">
          {financeData.expenses.title}
        </h3>
        <p className="text-xs font-bold text-text-muted">
          Track expenses per budget category and verify monthly spent ratios.
        </p>
      </div>

      <DashboardGrid>
        {financeData.expenses.items.map((item, idx) => {
          const Icon = LucideIcons[item.icon] || LucideIcons.Compass;
          const spentVal = parseFloat(item.spent.replace(/[^\d]/g, ''));
          const budgetVal = parseFloat(item.budget.replace(/[^\d]/g, ''));
          const pct = Math.round((spentVal / budgetVal) * 100);

          return (
            <motion.div
              key={item.category}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.05 }}
              className="lg:col-span-4 md:col-span-1"
            >
              <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 shadow-card flex flex-col justify-between gap-4 select-none relative group h-full">
                {/* Category Header */}
                <div className="flex items-center gap-3">
                  <div
                    className="p-2 rounded-xl flex items-center justify-center shrink-0 border shadow-xs"
                    style={{
                      background: `${item.color}12`,
                      color: item.color,
                      borderColor: `${item.color}25`,
                    }}
                  >
                    <Icon className="h-4.5 w-4.5 stroke-[2.2]" />
                  </div>
                  <div className="flex flex-col text-left">
                    <span className="text-xs font-black text-text-primary group-hover:text-primary transition-colors duration-200">
                      {item.category}
                    </span>
                    <span className="text-[10px] font-bold text-text-muted mt-0.5">
                      Budget limit: {item.budget}
                    </span>
                  </div>
                </div>

                {/* Progress bar info */}
                <div className="flex flex-col gap-1.5 mt-2">
                  <div className="flex justify-between items-center text-[10px] font-semibold text-text-secondary leading-none">
                    <span>Spent: {item.spent}</span>
                    <span className="font-bold text-text-primary">{pct}%</span>
                  </div>
                  <div className="w-full bg-muted h-2 rounded-full overflow-hidden border border-white/60 shadow-inner">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{ width: `${pct}%`, backgroundColor: item.color }}
                    />
                  </div>
                </div>
              </div>
            </motion.div>
          );
        })}

        {/* Premium Chart Placeholder */}
        <WidgetContainer
          title="Monthly Expense Category Distribution"
          icon="PieChart"
          sizeClass="lg:col-span-12"
        >
          <div className="flex flex-col md:flex-row items-center justify-around gap-6 py-4">
            {/* Visual Donut representation */}
            <div className="relative h-24 w-24 flex items-center justify-center shrink-0">
              <div className="absolute inset-0 rounded-full border-[10px] border-muted" />
              <div className="absolute inset-0 rounded-full border-[10px] border-transparent border-t-primary border-r-primary rotate-45" />
              <div className="absolute inset-0 rounded-full border-[10px] border-transparent border-b-accent rotate-[-45deg]" />
              <div className="h-10 w-10 rounded-full bg-card shadow-inner flex items-center justify-center text-xs font-black text-text-muted">
                OPEX
              </div>
            </div>

            {/* Legend checklist */}
            <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-left">
              {financeData.expenses.items.map((item) => (
                <div key={item.category} className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full shrink-0" style={{ backgroundColor: item.color }} />
                  <span className="text-xs font-bold text-text-secondary">{item.category}</span>
                </div>
              ))}
            </div>
          </div>
        </WidgetContainer>
      </DashboardGrid>
    </motion.div>
  );
}

export default Expenses;
