import React from 'react';
import { mockDatasets, Colors } from '@/config';
import { motion, useReducedMotion } from 'framer-motion';
import { DashboardGrid } from '@/components/dashboard';
import { LineChartCard, AreaChartCard } from '@/components/charts';
import { Badge } from '@/components/ui';

export function Monthly() {
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
          Monthly Financial Statement
        </h3>
        <p className="text-xs font-bold text-text-muted">
          Comprehensive monthly performance analysis, savings accumulation, and budget compliance.
        </p>
      </div>

      <DashboardGrid>
        {/* Monthly Line Trend */}
        <div className="lg:col-span-8 md:col-span-2 col-span-1">
          <LineChartCard
            title="Monthly Cash Inflow vs Outflow"
            subtitle="Income vs expense progression across 8 months"
            data={mockDatasets.incomeVsExpenses}
            xAxisKey="month"
            dataKeys={[
              { key: 'income', color: Colors.primary, name: 'Monthly Income' },
              { key: 'expenses', color: Colors.accent, name: 'Monthly Expenses' },
            ]}
            height={280}
          />
        </div>

        {/* Monthly Savings Growth Area */}
        <div className="lg:col-span-4 md:col-span-2 col-span-1">
          <AreaChartCard
            title="Monthly Savings Growth"
            subtitle="Net surplus saved per month"
            data={mockDatasets.incomeVsExpenses}
            xAxisKey="month"
            dataKeys={[
              { key: 'savings', color: Colors.success, name: 'Net Savings' },
            ]}
            height={280}
          />
        </div>
      </DashboardGrid>
    </motion.div>
  );
}

export default Monthly;
