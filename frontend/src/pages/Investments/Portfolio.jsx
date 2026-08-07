import React from 'react';
import { useProfile } from '@/hooks';
import { getInvestmentsConfig } from '@/config';
import { Badge, Button } from '@/components/ui';
import { motion, useReducedMotion } from 'framer-motion';
import { DashboardGrid, WidgetContainer, DashboardSection } from '@/components/dashboard';
import * as LucideIcons from 'lucide-react';

export function Portfolio() {
  const { profile } = useProfile();
  const shouldReduceMotion = useReducedMotion();
  const investData = getInvestmentsConfig(profile);

  if (!investData) {
    return (
      <div className="text-center p-8 text-text-muted">
        No active profile configuration found.
      </div>
    );
  }

  // Common activities list
  const activities = [
    { text: 'Sovereign Gold Bonds purchased', date: 'Today', type: 'gold', icon: 'Plus', color: '#F59E0B' },
    { text: 'Monthly Nifty Mutual Fund SIP processed', date: 'Yesterday', type: 'sip', icon: 'RefreshCw', color: '#7C3AED' },
    { text: 'Investment portfolio rebalanced', date: '3 days ago', type: 'system', icon: 'Check', color: '#10B981' },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 w-full text-left"
    >
      <DashboardGrid>
        
        {/* Core Portfolio Summary Metric Cards Row */}
        <div className="lg:col-span-12 grid grid-cols-1 sm:grid-cols-4 gap-6 bg-muted/20 border border-border/80 p-5 rounded-2xl">
          <div className="flex flex-col text-left pl-3 border-l-3 border-primary">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Total Portfolio Value
            </span>
            <span className="text-2xl font-extrabold text-text-primary tracking-tight mt-2.5">
              {investData.summary.totalValue}
            </span>
          </div>
          <div className="flex flex-col text-left border-l border-border/80 pl-4 border-l-3 border-success/80">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Today's Change
            </span>
            <span className="text-2xl font-extrabold text-success tracking-tight mt-2.5">
              {investData.summary.todayChange}
            </span>
          </div>
          <div className="flex flex-col text-left border-l border-border/80 pl-4 border-l-3 border-success/80">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Overall Return
            </span>
            <span className="text-2xl font-extrabold text-success tracking-tight mt-2.5">
              {investData.summary.overallReturn}
            </span>
          </div>
          <div className="flex flex-col border-l border-border/80 pl-4 justify-center">
            <Badge variant="secondary" className="mr-auto text-[10px] font-black uppercase bg-primary/10 border-primary/20 text-primary py-1 px-2.5 rounded">
              Risk: {investData.summary.riskLevel}
            </Badge>
          </div>
        </div>

        {/* Column 1: Asset Allocation Breakdown */}
        <WidgetContainer
          title="Asset Allocation Mix"
          icon="PieChart"
          sizeClass="lg:col-span-4 md:col-span-1"
        >
          <div className="flex flex-col gap-4 py-2">
            <div className="flex flex-col gap-3">
              {investData.holdings.map((hold) => (
                <div key={hold.name} className="flex justify-between items-center text-xs font-semibold">
                  <span className="text-text-secondary">{hold.name}</span>
                  <div className="flex items-center gap-2">
                    <span className="font-extrabold text-text-primary">{hold.value}</span>
                    <Badge variant="secondary" className="text-[8px] font-bold py-0.5 px-1 bg-muted text-text-muted border border-border">
                      {hold.allocation}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
            
            {/* Visual allocation progress strip */}
            <div className="w-full bg-muted h-3 rounded-full overflow-hidden border border-white/60 shadow-inner flex mt-2">
              <div className="bg-primary h-full" style={{ width: '60%' }} />
              <div className="bg-accent h-full" style={{ width: '30%' }} />
              <div className="bg-success h-full" style={{ width: '10%' }} />
            </div>
          </div>
        </WidgetContainer>

        {/* Column 2: Investment Activity Timeline */}
        <WidgetContainer
          title="Recent Portfolio Activity"
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
                  </div>
                );
              })}
            </div>
          </div>
        </WidgetContainer>

        {/* Smart AI insights summary */}
        <WidgetContainer
          title="Smart Portfolio Insights"
          icon="Sparkles"
          sizeClass="lg:col-span-12"
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 py-2">
            {investData.insights.map((ins, idx) => (
              <div key={idx} className="p-3.5 rounded-2xl bg-primary/5 border border-primary/10 flex gap-3.5 items-start hover:bg-primary/8 transition-colors duration-200 text-left">
                <div className="h-5 w-5 rounded-full bg-primary/10 flex items-center justify-center shrink-0 text-primary mt-0.5">
                  <LucideIcons.Sparkles className="h-3.5 w-3.5" />
                </div>
                <p className="text-xs font-semibold text-text-secondary leading-normal">
                  {ins.text}
                </p>
              </div>
            ))}
          </div>
        </WidgetContainer>

      </DashboardGrid>
    </motion.div>
  );
}

export default Portfolio;
