import React from 'react';
import { mockDatasets, Colors } from '@/config';
import { motion, useReducedMotion } from 'framer-motion';
import { DashboardGrid } from '@/components/dashboard';
import { ComposedChartCard, DonutChartCard } from '@/components/charts';

export function Weekly() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 w-full text-left select-none"
    >
      <div className="flex flex-col gap-1">
        <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">
          Weekly Performance Reports
        </h3>
        <p className="text-xs font-bold text-text-muted">
          Compare week-over-week spending efficiency, savings margins, and budget limits.
        </p>
      </div>

      <DashboardGrid>
        {/* Composed Chart: Budget vs Spent vs Savings */}
        <div className="lg:col-span-8 md:col-span-2 col-span-1">
          <ComposedChartCard
            title="Weekly Budget vs Actual Expenditure"
            subtitle="Comparing budget caps, actual debits, and weekly net savings"
            data={mockDatasets.weeklyPerformance}
            xAxisKey="week"
            barKeys={[
              { key: 'spent', color: Colors.primary, name: 'Spent' },
              { key: 'saved', color: Colors.success, name: 'Saved' },
            ]}
            lineKeys={[
              { key: 'budget', color: Colors.accent, name: 'Budget Cap' },
            ]}
            height={280}
          />
        </div>

        {/* Weekly Category Breakdown */}
        <div className="lg:col-span-4 md:col-span-2 col-span-1">
          <DonutChartCard
            title="Weekly Category Breakdown"
            subtitle="Distribution of weekly debits"
            data={mockDatasets.expenseCategories}
            height={280}
          />
        </div>
      </DashboardGrid>
    </motion.div>
  );
}

export default Weekly;
