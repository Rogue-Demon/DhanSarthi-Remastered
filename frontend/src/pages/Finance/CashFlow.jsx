import React from 'react';
import { useProfile } from '@/hooks';
import { getFinanceConfig } from '@/config';
import { motion, useReducedMotion } from 'framer-motion';
import { DashboardGrid, WidgetContainer } from '@/components/dashboard';
import * as LucideIcons from 'lucide-react';
import { Badge } from '@/components/ui';

export function CashFlow() {
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
          Cash Flow Statement
        </h3>
        <p className="text-xs font-bold text-text-muted">
          Analyze inbound incomes against outbound payments and outstanding receivables.
        </p>
      </div>

      <DashboardGrid>
        
        {/* Money In */}
        <div className="lg:col-span-4 md:col-span-1">
          <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 shadow-card flex items-center justify-between gap-4 select-none relative group h-full">
            <div className="absolute left-0 top-0 bottom-0 w-1 bg-success transition-all duration-300 group-hover:w-1.5" />
            <div className="flex flex-col gap-1.5 pl-2 text-left">
              <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                Total Inbound (In)
              </span>
              <span className="text-2xl font-black text-text-primary tracking-tight leading-none">
                {financeData.cashFlow.income}
              </span>
              <span className="text-[10px] font-bold text-success mt-0.5">
                Invoices collected
              </span>
            </div>
            <div className="p-3.5 rounded-2xl flex items-center justify-center border bg-success/10 text-success shadow-xs shrink-0">
              <LucideIcons.ArrowUpRight className="h-5 w-5 stroke-[2px]" />
            </div>
          </div>
        </div>

        {/* Money Out */}
        <div className="lg:col-span-4 md:col-span-1">
          <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 shadow-card flex items-center justify-between gap-4 select-none relative group h-full">
            <div className="absolute left-0 top-0 bottom-0 w-1 bg-danger transition-all duration-300 group-hover:w-1.5" />
            <div className="flex flex-col gap-1.5 pl-2 text-left">
              <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                Total Outbound (Out)
              </span>
              <span className="text-2xl font-black text-text-primary tracking-tight leading-none">
                {financeData.cashFlow.expense}
              </span>
              <span className="text-[10px] font-bold text-danger mt-0.5">
                Bill payments debited
              </span>
            </div>
            <div className="p-3.5 rounded-2xl flex items-center justify-center border bg-danger/10 text-danger shadow-xs shrink-0">
              <LucideIcons.ArrowDownLeft className="h-5 w-5 stroke-[2px]" />
            </div>
          </div>
        </div>

        {/* Net surplus */}
        <div className="lg:col-span-4 md:col-span-1">
          <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 shadow-card flex items-center justify-between gap-4 select-none relative group h-full">
            <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary transition-all duration-300 group-hover:w-1.5" />
            <div className="flex flex-col gap-1.5 pl-2 text-left">
              <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                Net cash flow yield
              </span>
              <span className="text-2xl font-black text-text-primary tracking-tight leading-none">
                {financeData.cashFlow.netFlow}
              </span>
              <span className="text-[10px] font-bold text-primary mt-0.5">
                Liquid cushion added
              </span>
            </div>
            <div className="p-3.5 rounded-2xl flex items-center justify-center border bg-primary/10 text-primary shadow-xs shrink-0">
              <LucideIcons.RefreshCw className="h-5 w-5 stroke-[2px]" />
            </div>
          </div>
        </div>

        {/* Cash Flow Timeline chart placeholder */}
        <WidgetContainer
          title="Cash Flow Accumulation Chart"
          icon="TrendingUp"
          sizeClass="lg:col-span-12"
        >
          <div className="h-32 w-full rounded-2xl bg-card border border-border/80 relative flex items-end justify-between px-8 pb-3 overflow-hidden mt-2">
            <div className="absolute inset-0 opacity-[0.02] bg-[radial-gradient(#7C3AED_1px,transparent_1px)] [background-size:12px_12px]" />
            
            {/* Visual graph line paths */}
            <svg className="absolute inset-0 w-full h-full text-success/10" preserveAspectRatio="none" viewBox="0 0 100 100">
              <path d="M0,90 Q20,80 40,85 T80,50 T100,30 L100,100 Z" fill="currentColor" />
              <path d="M0,90 Q20,80 40,85 T80,50 T100,30" fill="none" stroke="#10B981" strokeWidth="2.5" />
            </svg>

            {['Week 1', 'Week 2', 'Week 3', 'Week 4'].map((w) => (
              <span key={w} className="text-[9px] font-black text-text-muted z-10">{w}</span>
            ))}
          </div>
        </WidgetContainer>
      </DashboardGrid>
    </motion.div>
  );
}

export default CashFlow;
