import React from 'react';
import { mockDatasets, Colors } from '@/config';
import { motion, useReducedMotion } from 'framer-motion';
import { DashboardGrid } from '@/components/dashboard';
import { AreaChartCard, BarChartCard } from '@/components/charts';
import * as LucideIcons from 'lucide-react';
import { Badge } from '@/components/ui';

export function Annual() {
  const shouldReduceMotion = useReducedMotion();

  const milestones = [
    { year: '2026', title: 'Crossed ₹15 Lakhs Portfolio Net Worth', icon: 'Trophy', color: '#10B981' },
    { year: '2025', title: 'Achieved 6-Month Emergency Fund Target', icon: 'Shield', color: '#7C3AED' },
    { year: '2024', title: 'Started Systematic SIP Investment Plan', icon: 'TrendingUp', color: '#3B82F6' },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 w-full text-left select-none"
    >
      <div className="flex flex-col gap-1">
        <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">
          Annual Performance & 5-Year Growth
        </h3>
        <p className="text-xs font-bold text-text-muted">
          Multi-year revenue, net worth growth trajectories, and financial milestone accomplishments.
        </p>
      </div>

      <DashboardGrid>
        {/* 5-Year Net Worth Area Chart */}
        <div className="lg:col-span-8 md:col-span-2 col-span-1">
          <AreaChartCard
            title="5-Year Net Worth Progression"
            subtitle="Multi-year accumulation (2022 - 2026)"
            data={mockDatasets.annualGrowth}
            xAxisKey="year"
            dataKeys={[
              { key: 'netWorth', color: Colors.primary, name: 'Net Worth Value' },
              { key: 'revenue', color: Colors.success, name: 'Annual Income' },
            ]}
            height={280}
          />
        </div>

        {/* Milestones Card */}
        <div className="lg:col-span-4 md:col-span-2 col-span-1">
          <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl shadow-card flex flex-col gap-4 text-left h-full">
            <h4 className="text-xs font-black text-text-primary uppercase tracking-wider">
              Annual Milestones
            </h4>

            <div className="flex flex-col gap-3">
              {milestones.map((m, i) => {
                const Icon = LucideIcons[m.icon] || LucideIcons.Award;
                return (
                  <div key={i} className="p-3 rounded-xl bg-muted/30 border border-border/60 flex items-start gap-3">
                    <div className="p-2 rounded-lg text-white shrink-0" style={{ backgroundColor: m.color }}>
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="flex flex-col gap-0.5">
                      <span className="text-[10px] font-black text-text-muted">{m.year}</span>
                      <span className="text-xs font-bold text-text-primary">{m.title}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </DashboardGrid>
    </motion.div>
  );
}

export default Annual;
