import React from 'react';
import { useProfile } from '@/hooks';
import { getFinanceConfig } from '@/config';
import { motion, useReducedMotion } from 'framer-motion';
import { DashboardGrid, WidgetContainer } from '@/components/dashboard';
import * as LucideIcons from 'lucide-react';
import { Badge } from '@/components/ui';

export function Income() {
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
          {financeData.income.title}
        </h3>
        <p className="text-xs font-bold text-text-muted">
          Detailed breakdown of your incoming credits and active salary pipelines.
        </p>
      </div>

      <DashboardGrid>
        {financeData.income.items.map((item, idx) => {
          const Icon = LucideIcons[item.icon] || LucideIcons.TrendingUp;

          return (
            <motion.div
              key={item.label}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.05 }}
              className="lg:col-span-4 md:col-span-1"
            >
              <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 shadow-card flex items-center justify-between gap-4 select-none relative group overflow-hidden h-full">
                {/* Visual bar glow accent */}
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary transition-all duration-300 group-hover:w-1.5" />

                <div className="flex flex-col gap-1.5 pl-2 text-left">
                  <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                    {item.label}
                  </span>
                  <span className="text-2xl font-black text-text-primary tracking-tight leading-none">
                    {item.value}
                  </span>
                  <span className="text-[10px] font-bold text-text-secondary">
                    {item.desc}
                  </span>
                </div>

                <div className="p-3.5 rounded-2xl flex items-center justify-center border border-white/40 dark:border-white/5 bg-primary/10 text-primary shadow-xs shrink-0">
                  <Icon className="h-5 w-5 stroke-[2px]" />
                </div>
              </div>
            </motion.div>
          );
        })}

        {/* Premium Chart Placeholder */}
        <WidgetContainer
          title="Income vs Expenses Trends"
          icon="LineChart"
          sizeClass="lg:col-span-12"
        >
          <div className="h-32 w-full rounded-2xl bg-card/65 border border-border/80 relative flex items-end justify-between px-8 pb-3 overflow-hidden mt-2">
            <div className="absolute inset-0 opacity-[0.02] bg-[radial-gradient(#7C3AED_1px,transparent_1px)] [background-size:12px_12px]" />
            
            {/* Visual graph path */}
            <svg className="absolute inset-0 w-full h-full text-primary/15" preserveAspectRatio="none" viewBox="0 0 100 100">
              <path d="M0,90 Q20,60 40,80 T80,40 T100,20 L100,100 Z" fill="currentColor" />
              <path d="M0,90 Q20,60 40,80 T80,40 T100,20" fill="none" stroke="var(--primary)" strokeWidth="2" />
            </svg>

            {['Apr', 'May', 'Jun', 'Jul', 'Aug'].map((m) => (
              <span key={m} className="text-[9px] font-black text-text-muted z-10">{m}</span>
            ))}

            <div className="absolute top-3 right-4 flex items-center gap-1.5 text-[10px] font-bold text-text-muted">
              <LucideIcons.Sparkles className="h-3.5 w-3.5 text-accent animate-pulse" />
              <span>Yield forecast is positive</span>
            </div>
          </div>
        </WidgetContainer>
      </DashboardGrid>
    </motion.div>
  );
}

export default Income;
