import React from 'react';
import { useProfile } from '@/hooks';
import { getReportsConfig, mockDatasets, Colors } from '@/config';
import { motion, useReducedMotion } from 'framer-motion';
import { DashboardGrid } from '@/components/dashboard';
import {
  AreaChartCard,
  DonutChartCard,
  BarChartCard,
  MiniTrendChart,
} from '@/components/charts';
import * as LucideIcons from 'lucide-react';
import { Badge } from '@/components/ui';

export function Overview() {
  const { profile } = useProfile();
  const shouldReduceMotion = useReducedMotion();
  const reportsData = getReportsConfig(profile);

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 w-full text-left"
    >
      {/* Executive KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {reportsData.focusMetrics.map((metric, idx) => {
          const Icon = LucideIcons[metric.icon] || LucideIcons.Activity;

          return (
            <motion.div
              key={metric.title}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.05 }}
              className="clay-surface bg-card p-4 border border-white/60 dark:border-white/5 shadow-card flex items-center justify-between gap-3 select-none text-left"
            >
              <div className="flex flex-col gap-1">
                <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                  {metric.title}
                </span>
                <span className="text-xl font-black text-text-primary tracking-tight">
                  {metric.value}
                </span>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <Badge variant="secondary" className="text-[8px] font-bold py-0.5 px-1 bg-success/10 text-success border-success/15 rounded">
                    {metric.change}
                  </Badge>
                  <span className="text-[9px] font-bold text-text-muted">{metric.status}</span>
                </div>
              </div>

              <div className="flex flex-col items-end gap-2">
                <div className="p-2 rounded-xl bg-primary/10 text-primary shrink-0">
                  <Icon className="h-4 w-4" />
                </div>
                {/* Mini Sparkline Chart */}
                <MiniTrendChart data={[12, 18, 14, 22, 28, 25, 34]} color={Colors.primary} width={60} height={24} />
              </div>
            </motion.div>
          );
        })}
      </div>

      <DashboardGrid>
        {/* Main Income vs Expense Area Chart */}
        <div className="lg:col-span-8 md:col-span-2 col-span-1">
          <AreaChartCard
            title="Income vs Expenses Trends"
            subtitle="Monthly inbound credits vs outbound expenditures (2026)"
            data={mockDatasets.incomeVsExpenses}
            xAxisKey="month"
            dataKeys={[
              { key: 'income', color: Colors.primary, name: 'Income' },
              { key: 'expenses', color: Colors.accent, name: 'Expenses' },
            ]}
            height={280}
          />
        </div>

        {/* Expense Category Donut Chart */}
        <div className="lg:col-span-4 md:col-span-2 col-span-1">
          <DonutChartCard
            title="Expense Allocations"
            subtitle="Breakdown by operational category"
            data={mockDatasets.expenseCategories}
            height={280}
          />
        </div>

        {/* Weekly Savings Bar Chart */}
        <div className="lg:col-span-6 md:col-span-2 col-span-1">
          <BarChartCard
            title="Weekly Budget vs Actual Spend"
            subtitle="Comparison across recent 4 weeks"
            data={mockDatasets.weeklyPerformance}
            xAxisKey="week"
            dataKeys={[
              { key: 'budget', color: Colors.secondary, name: 'Budget Target' },
              { key: 'spent', color: Colors.primary, name: 'Actual Spent' },
            ]}
            height={260}
          />
        </div>

        {/* AI Highlights Panel */}
        <div className="lg:col-span-6 md:col-span-2 col-span-1 flex flex-col gap-4">
          <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl shadow-card flex flex-col gap-4 text-left h-full">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-black text-text-primary uppercase tracking-wider">
                AI Executive Highlights
              </h4>
              <LucideIcons.Sparkles className="h-4 w-4 text-accent" />
            </div>

            <div className="flex flex-col gap-3">
              {reportsData.highlights.map((h, i) => (
                <div key={i} className="p-3 rounded-xl bg-primary/5 border border-primary/10 flex items-start gap-3">
                  <LucideIcons.CheckCircle2 className="h-4 w-4 text-success shrink-0 mt-0.5" />
                  <p className="text-xs font-semibold text-text-secondary leading-relaxed">
                    {h.text}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </DashboardGrid>
    </motion.div>
  );
}

export default Overview;
