import React from 'react';
import { useProfile } from '@/hooks';
import { getFinanceConfig } from '@/config';
import { Badge, Button } from '@/components/ui';
import { motion, useReducedMotion } from 'framer-motion';
import { DashboardGrid, WidgetContainer, DashboardSection } from '@/components/dashboard';
import * as LucideIcons from 'lucide-react';

export function Overview() {
  const { profile } = useProfile();
  const shouldReduceMotion = useReducedMotion();
  const financeData = getFinanceConfig(profile);

  if (!financeData) {
    return (
      <div className="text-center p-8 text-text-muted">
        No active profile configuration found.
      </div>
    );
  }

  // Common activities list
  const activities = [
    { text: 'Cash reserve deposit added', value: '+₹4,200', date: 'Today', icon: 'Plus', color: '#10B981' },
    { text: 'Logged monthly utilities charge', value: '-₹3,150', date: 'Yesterday', icon: 'Minus', color: '#EF4444' },
    { text: 'Budget targets updated', value: 'Info', date: '3 days ago', icon: 'Check', color: '#8B5CF6' },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 w-full text-left"
    >
      <DashboardGrid>
        
        {/* Core Financial Summary Metric Row */}
        <div className="lg:col-span-12 grid grid-cols-1 sm:grid-cols-3 gap-6 bg-muted/20 border border-border/80 p-5 rounded-2xl">
          <div className="flex flex-col text-left pl-3 border-l-3 border-primary">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Inflows (Income)
            </span>
            <span className="text-2xl font-extrabold text-text-primary tracking-tight mt-2.5">
              {financeData.cashFlow.income}
            </span>
          </div>
          <div className="flex flex-col text-left border-x border-border/80 px-6 pl-6 border-l-3 border-danger/80">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Outflows (Expenses)
            </span>
            <span className="text-2xl font-extrabold text-text-primary tracking-tight mt-2.5">
              {financeData.cashFlow.expense}
            </span>
          </div>
          <div className="flex flex-col text-left pl-6 border-l-3 border-success/80">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Net Surplus (Flow)
            </span>
            <span className="text-2xl font-extrabold text-text-primary tracking-tight mt-2.5">
              {financeData.cashFlow.netFlow}
            </span>
          </div>
        </div>

        {/* Column 1: Financial Health Indicator */}
        <WidgetContainer
          title="Financial Health Score"
          icon="Activity"
          sizeClass="lg:col-span-4 md:col-span-1"
        >
          <div className="flex flex-col items-center justify-center text-center gap-4 py-2">
            <div className="relative h-20 w-20 flex items-center justify-center">
              <svg className="h-full w-full transform -rotate-90" viewBox="0 0 36 36">
                <path className="text-muted" strokeWidth="3" stroke="currentColor" fill="transparent" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                <path className="text-primary" strokeWidth="3" strokeDasharray="80, 100" strokeLinecap="round" stroke="currentColor" fill="transparent" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
              </svg>
              <span className="absolute text-base font-black text-text-primary">80%</span>
            </div>
            <div className="flex flex-col gap-1">
              <Badge variant="secondary" className="mx-auto text-[9px] font-bold bg-primary/10 text-primary border-primary/20 py-0.5 px-2 rounded">
                Stable Health
              </Badge>
              <p className="text-[10px] font-bold text-text-muted leading-relaxed max-w-[180px] mt-1.5">
                Investments allocations are healthy. Keep utility expenses controlled.
              </p>
            </div>
          </div>
        </WidgetContainer>

        {/* Column 2: Recent Activity Timeline */}
        <WidgetContainer
          title="Ledger Timeline"
          icon="History"
          sizeClass="lg:col-span-8 md:col-span-2"
        >
          <div className="flex flex-col gap-4 py-1 text-left">
            <div className="flex flex-col gap-3.5 border-l border-border/80 ml-2 pl-4 relative">
              {activities.map((act, idx) => {
                const Icon = LucideIcons[act.icon] || LucideIcons.Info;
                return (
                  <div key={idx} className="flex justify-between items-center text-xs relative group">
                    <div className="absolute left-[-21.5px] top-[4px] h-3.5 w-3.5 rounded-full border-2 border-card bg-primary flex items-center justify-center text-white">
                      <Icon className="h-1.5 w-1.5 stroke-[2.5]" />
                    </div>
                    <div className="flex flex-col gap-0.5">
                      <span className="font-extrabold text-text-primary group-hover:text-primary transition-colors duration-200">{act.text}</span>
                      <span className="text-[9px] font-bold text-text-muted">{act.date}</span>
                    </div>
                    <span className="font-black text-text-secondary">{act.value}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </WidgetContainer>

        {/* Goal summary list */}
        <WidgetContainer
          title="Active Goal Target Summary"
          icon="Target"
          sizeClass="lg:col-span-12"
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 py-2">
            {financeData.goals.map((goal) => {
              const GoalIcon = LucideIcons[goal.icon] || LucideIcons.Compass;
              const pct = Math.round((goal.current / goal.target) * 100);

              return (
                <div key={goal.name} className="flex items-center gap-4 bg-muted/30 border border-border p-3.5 rounded-xl text-left select-none relative group hover:border-primary/20 transition-all duration-200">
                  <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0 border">
                    <GoalIcon className="h-5 w-5" />
                  </div>
                  <div className="flex-1 flex flex-col gap-1">
                    <div className="flex justify-between text-xs font-black text-text-primary leading-none">
                      <span>{goal.name}</span>
                      <span>{pct}%</span>
                    </div>
                    <div className="w-full bg-muted h-2 rounded-full mt-1.5 overflow-hidden border border-white/60">
                      <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, backgroundColor: goal.color }} />
                    </div>
                    <div className="flex justify-between items-center text-[9px] font-bold text-text-muted mt-1 uppercase tracking-wider">
                      <span>Saved: ₹{goal.current}</span>
                      <span>Target: ₹{goal.target}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </WidgetContainer>

      </DashboardGrid>
    </motion.div>
  );
}

export default Overview;
