import React from 'react';
import { useProfile } from '@/hooks';
import { getAIAdvisorConfig } from '@/config';
import { Badge } from '@/components/ui';
import * as LucideIcons from 'lucide-react';
import { cn } from '@/utils';

/**
 * InsightPanel Component
 * Right-side panel for the AI Advisor workspace displaying real-time financial health,
 * today's AI insights, recommended actions, and upcoming reminders.
 */
export function InsightPanel({ className }) {
  const { profile } = useProfile();
  const advisorConfig = getAIAdvisorConfig(profile);

  return (
    <aside
      className={cn(
        'hidden lg:flex flex-col w-72 shrink-0 bg-card border-l border-border/80 h-full p-4 gap-5 overflow-y-auto scrollbar-none text-left select-none',
        className
      )}
    >
      {/* Financial Health Score Widget */}
      <div className="clay-surface bg-card p-4 border border-white/60 dark:border-white/5 rounded-2xl flex flex-col gap-3 shadow-xs">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
            AI Health Monitor
          </span>
          <Badge variant="secondary" className="text-[8px] font-bold py-0.5 px-1.5 bg-success/10 text-success border-success/15 rounded">
            Optimal
          </Badge>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative h-12 w-12 flex items-center justify-center shrink-0">
            <svg className="h-full w-full transform -rotate-90" viewBox="0 0 36 36">
              <path className="text-muted" strokeWidth="4" stroke="currentColor" fill="transparent" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
              <path className="text-primary" strokeWidth="4" strokeDasharray="82, 100" strokeLinecap="round" stroke="currentColor" fill="transparent" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
            </svg>
            <span className="absolute text-xs font-black text-text-primary">82%</span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-xs font-black text-text-primary">Financial Fitness</span>
            <span className="text-[10px] font-bold text-text-muted">High liquidity & savings</span>
          </div>
        </div>
      </div>

      {/* Profile-Specific Insights */}
      <div className="flex flex-col gap-2.5">
        <span className="text-[9px] font-black text-text-muted uppercase tracking-widest px-1">
          Today's AI Insights
        </span>
        {advisorConfig.insights.map((ins, idx) => {
          const Icon = LucideIcons[ins.icon] || LucideIcons.Sparkles;

          return (
            <div key={idx} className="flex items-center justify-between p-3 rounded-xl bg-muted/30 border border-border/60 text-xs">
              <div className="flex items-center gap-2.5">
                <div className="p-1.5 rounded-lg text-white shrink-0" style={{ backgroundColor: ins.color }}>
                  <Icon className="h-3.5 w-3.5" />
                </div>
                <span className="font-extrabold text-text-primary">{ins.title}</span>
              </div>
              <span className="font-black text-text-secondary text-[11px]">{ins.value}</span>
            </div>
          );
        })}
      </div>

      {/* Recommended Quick Actions */}
      <div className="flex flex-col gap-2.5">
        <span className="text-[9px] font-black text-text-muted uppercase tracking-widest px-1">
          Recommended Actions
        </span>
        {advisorConfig.quickActions.map((act, idx) => {
          const Icon = LucideIcons[act.icon] || LucideIcons.Zap;

          return (
            <button
              key={idx}
              onClick={() => console.log('Action clicked:', act.label)}
              className="flex items-center justify-between p-3 rounded-xl bg-card border border-border hover:border-primary/30 transition-all text-xs font-bold text-text-primary hover:text-primary group cursor-pointer"
            >
              <div className="flex items-center gap-2.5">
                <Icon className="h-4 w-4 text-primary shrink-0" />
                <span>{act.label}</span>
              </div>
              <LucideIcons.ChevronRight className="h-3.5 w-3.5 text-text-muted group-hover:text-primary transition-colors" />
            </button>
          );
        })}
      </div>

      {/* Upcoming Reminders Placeholder */}
      <div className="flex flex-col gap-2.5 pt-2 border-t border-border/60">
        <span className="text-[9px] font-black text-text-muted uppercase tracking-widest px-1">
          Upcoming Reminders
        </span>
        <div className="p-3 rounded-xl bg-warning/10 border border-warning/20 flex flex-col gap-1 text-left">
          <div className="flex items-center justify-between text-[10px] font-black text-warning">
            <span className="uppercase tracking-wider">SIP Auto-Debit</span>
            <span>05th Aug</span>
          </div>
          <p className="text-xs font-bold text-text-primary mt-0.5">
            ₹10,000 HDFC Mid-Cap SIP debit scheduled.
          </p>
        </div>
      </div>
    </aside>
  );
}

export default InsightPanel;
