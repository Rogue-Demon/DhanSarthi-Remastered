import React from 'react';
import { mockDatasets, Colors } from '@/config';
import { motion, useReducedMotion } from 'framer-motion';
import { DashboardGrid } from '@/components/dashboard';
import { BarChartCard } from '@/components/charts';
import { Badge } from '@/components/ui';

export function Goals() {
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
          Financial Goals Analytics
        </h3>
        <p className="text-xs font-bold text-text-muted">
          Track savings milestone achievement rates, goal target progress, and completion timelines.
        </p>
      </div>

      <DashboardGrid>
        {/* Goal Progress Bar Chart */}
        <div className="lg:col-span-8 md:col-span-2 col-span-1">
          <BarChartCard
            title="Goal Target vs Current Saved"
            subtitle="Comparing saved capital against target goal limits"
            data={mockDatasets.goalsAnalytics}
            xAxisKey="goal"
            dataKeys={[
              { key: 'current', color: Colors.primary, name: 'Current Saved' },
              { key: 'target', color: Colors.secondary, name: 'Target Amount' },
            ]}
            height={280}
          />
        </div>

        {/* Goal Stats Summary */}
        <div className="lg:col-span-4 md:col-span-2 col-span-1">
          <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl shadow-card flex flex-col gap-4 text-left h-full">
            <h4 className="text-xs font-black text-text-primary uppercase tracking-wider">
              Goal Achievement Score
            </h4>

            <div className="flex flex-col gap-3">
              <div className="flex justify-between items-center text-xs font-semibold p-3 rounded-xl bg-muted/30 border border-border/60">
                <span className="text-text-secondary">Completed Goals</span>
                <span className="font-extrabold text-success">1 Goal (100%)</span>
              </div>
              <div className="flex justify-between items-center text-xs font-semibold p-3 rounded-xl bg-muted/30 border border-border/60">
                <span className="text-text-secondary">Active In-Progress Goals</span>
                <span className="font-extrabold text-primary">3 Goals</span>
              </div>
              <div className="flex justify-between items-center text-xs font-semibold p-3 rounded-xl bg-primary/10 border border-primary/20">
                <span className="text-primary font-black">Overall Achievement Rate</span>
                <span className="font-extrabold text-primary">71%</span>
              </div>
            </div>
          </div>
        </div>
      </DashboardGrid>
    </motion.div>
  );
}

export default Goals;
