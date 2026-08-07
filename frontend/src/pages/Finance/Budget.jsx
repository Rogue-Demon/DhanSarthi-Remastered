import React from 'react';
import { useProfile } from '@/hooks';
import { getFinanceConfig } from '@/config';
import { motion, useReducedMotion } from 'framer-motion';
import { DashboardGrid, WidgetContainer } from '@/components/dashboard';
import * as LucideIcons from 'lucide-react';
import { Badge } from '@/components/ui';

export function Budget() {
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
          Financial Budget Tracker
        </h3>
        <p className="text-xs font-bold text-text-muted">
          Compare total budget limits, actual expenditures, and remaining balances.
        </p>
      </div>

      <DashboardGrid>
        
        {/* Core summary card */}
        <div className="lg:col-span-12 grid grid-cols-1 sm:grid-cols-4 gap-4 bg-muted/20 border border-border/85 p-5 rounded-2xl">
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">Total Budget Limit</span>
            <span className="text-xl font-extrabold text-text-primary mt-1">{financeData.budget.allowance}</span>
          </div>
          <div className="flex flex-col border-l border-border/80 pl-4">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">Spent to Date</span>
            <span className="text-xl font-extrabold text-primary mt-1">{financeData.budget.spent}</span>
          </div>
          <div className="flex flex-col border-l border-border/80 pl-4">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">Remaining Balance</span>
            <span className="text-xl font-extrabold text-success mt-1">{financeData.budget.remaining}</span>
          </div>
          <div className="flex flex-col border-l border-border/80 pl-4 justify-center">
            <Badge variant="secondary" className="mr-auto text-[10px] font-black uppercase bg-primary/10 border-primary/20 text-primary py-1 px-2.5 rounded">
              {financeData.budget.status}
            </Badge>
          </div>
        </div>

        {/* Column 1: Spent Ratio Progress Bar */}
        <WidgetContainer
          title="Overall Budget Progress"
          icon="PieChart"
          sizeClass="lg:col-span-4 md:col-span-1"
        >
          <div className="flex flex-col justify-center items-start gap-4 py-2 text-left">
            <div className="flex justify-between items-center w-full text-xs font-bold text-text-secondary leading-none">
              <span>Spent Margin Limit</span>
              <span className="text-primary font-black">{financeData.budget.progress}% spent</span>
            </div>
            <div className="w-full bg-muted h-3 rounded-full overflow-hidden border border-white/60 shadow-inner">
              <div className="bg-gradient-primary h-full rounded-full" style={{ width: `${financeData.budget.progress}%` }} />
            </div>
            <span className="text-[10px] font-bold text-text-muted leading-relaxed">
              Based on active opex, you have ₹{financeData.budget.remaining} liquid cash remaining.
            </span>
          </div>
        </WidgetContainer>

        {/* Column 2: Savings Opportunity */}
        <WidgetContainer
          title="Savings Opportunity"
          icon="TrendingUp"
          sizeClass="lg:col-span-8 md:col-span-2"
        >
          <div className="flex items-start gap-4 py-1 text-left select-none relative group">
            <div className="h-10 w-10 rounded-xl bg-success/15 border border-success/20 text-success flex items-center justify-center shrink-0">
              <LucideIcons.Sparkles className="h-5 w-5" />
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-xs font-black text-text-primary leading-none uppercase">AI Recommendation</span>
              <p className="text-xs font-semibold text-text-secondary leading-relaxed mt-1">
                By capping utility and dining out categories, you can redirect an estimated <span className="text-success font-extrabold">₹1,500</span> directly to your MacBook saving targets!
              </p>
            </div>
          </div>
        </WidgetContainer>
      </DashboardGrid>
    </motion.div>
  );
}

export default Budget;
