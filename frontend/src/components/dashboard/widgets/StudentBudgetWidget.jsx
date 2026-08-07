import React from 'react';
import { Badge, Button } from '@/components/ui';
import * as LucideIcons from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import WidgetContainer from '../WidgetContainer';
import WidgetActions from '../WidgetActions';

export function StudentBudgetWidget({ widget, sizeClass }) {
  const shouldReduceMotion = useReducedMotion();

  // Mock recommended actions
  const actions = [
    { title: 'Review Monthly Budget', desc: 'You spent 64% of your allowance.', icon: 'CheckSquare', color: '#10B981' },
    { title: 'Explore Micro-Investments', desc: 'Start a small SIP starting at ₹100.', icon: 'TrendingUp', color: '#8B5CF6' },
  ];

  const toolbar = (
    <WidgetActions
      onInfo={() => alert('Information on Budget Planning')}
      onRefresh={() => console.log('Budget refresh')}
    />
  );

  return (
    <WidgetContainer
      title={widget.title}
      icon={widget.icon}
      color={widget.color}
      sizeClass={sizeClass}
      toolbar={toolbar}
    >
      <div className="flex flex-col gap-6 h-full select-none text-left">
        {/* Metrics Row: Allowance vs Spent vs Remaining */}
        <div className="grid grid-cols-3 gap-4 bg-muted/30 border border-border p-4.5 rounded-2xl">
          <div className="flex flex-col text-left">
            <span className="text-[10px] font-black text-text-muted uppercase tracking-wider leading-none">
              Allowance
            </span>
            <span className="text-lg font-black text-text-primary mt-1.5">
              ₹5,000
            </span>
          </div>
          <div className="flex flex-col text-left border-x border-border/80 px-4">
            <span className="text-[10px] font-black text-text-muted uppercase tracking-wider leading-none">
              Spent
            </span>
            <span className="text-lg font-black text-primary mt-1.5">
              ₹3,200
            </span>
          </div>
          <div className="flex flex-col text-left pl-2">
            <span className="text-[10px] font-black text-text-muted uppercase tracking-wider leading-none">
              Remaining
            </span>
            <span className="text-lg font-black text-success mt-1.5">
              ₹1,800
            </span>
          </div>
        </div>

        {/* Progress visualizer strip */}
        <div className="flex flex-col gap-1.5">
          <div className="flex justify-between items-center text-[10px] font-black text-text-muted uppercase tracking-wider">
            <span>Monthly Progress Limit</span>
            <span className="text-primary font-black">64% spent</span>
          </div>
          <div className="w-full bg-muted h-3 rounded-full overflow-hidden border border-white/60 shadow-inner relative">
            {/* Glowing bar */}
            <div
              className="bg-gradient-primary h-full rounded-full transition-all duration-500 shadow-button"
              style={{ width: '64%' }}
            />
          </div>
        </div>

        {/* Reusable action cards */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <LucideIcons.ListChecks className="h-4 w-4 text-text-muted" />
            <h4 className="text-xs font-black text-text-muted uppercase tracking-wider">
              Recommended Actions
            </h4>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {actions.map((act, idx) => {
              const ActIcon = LucideIcons[act.icon] || LucideIcons.Compass;
              return (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: idx * 0.05 }}
                  className="clay-surface bg-card p-3 border border-white/60 dark:border-white/5 shadow-card flex flex-col justify-between items-start gap-3 hover:border-primary/20 transition-all duration-200"
                >
                  <div className="flex items-start gap-2">
                    <div
                      className="p-1.5 rounded-lg flex items-center justify-center text-white shrink-0 mt-0.5"
                      style={{ background: act.color }}
                    >
                      <ActIcon className="h-3.5 w-3.5" />
                    </div>
                    <div className="flex flex-col gap-0.5">
                      <span className="text-xs font-black text-text-primary leading-tight">
                        {act.title}
                      </span>
                      <span className="text-[10px] font-bold text-text-muted leading-relaxed">
                        {act.desc}
                      </span>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="xs"
                    className="p-0 text-primary font-black uppercase text-[9px] hover:bg-transparent"
                    onClick={() => alert(`Trigger action: ${act.title}`)}
                    iconRight={<LucideIcons.ArrowRight className="h-3 w-3" />}
                  >
                    Action
                  </Button>
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* Chart Placeholder: Allowance vs Spending */}
        <div className="flex flex-col gap-2.5 border-t border-border/50 pt-4 mt-auto">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-black text-text-muted uppercase tracking-wider">
              Allowance vs Spending Trends
            </h4>
            <span className="text-[9px] font-black text-text-muted uppercase tracking-wider">
              Weekly review
            </span>
          </div>

          {/* Mock comparison graph */}
          <div className="h-20 w-full rounded-2xl bg-card border border-border/70 relative flex items-end justify-between px-6 py-2.5 overflow-hidden">
            <div className="absolute inset-0 opacity-[0.02] bg-[radial-gradient(#7C3AED_1px,transparent_1px)] [background-size:10px_10px]" />
            
            {/* Vertical Bar chart visual blocks */}
            {['Week 1', 'Week 2', 'Week 3', 'Week 4'].map((week, idx) => {
              const allowanceVal = [30, 45, 55, 40][idx];
              const spendVal = [55, 30, 65, 45][idx];
              return (
                <div key={week} className="flex items-end gap-1.5 h-full relative">
                  {/* Allowance bar */}
                  <div
                    className="w-2.5 rounded-t-sm transition-all duration-500"
                    style={{
                      height: `${allowanceVal}%`,
                      background: 'rgba(124, 58, 237, 0.15)',
                    }}
                  />
                  {/* Spend bar */}
                  <div
                    className="w-2.5 rounded-t-sm transition-all duration-500"
                    style={{
                      height: `${spendVal}%`,
                      background: 'var(--gradient-primary)',
                    }}
                  />
                  <span className="absolute bottom-[-16px] left-1/2 -translate-x-1/2 text-[8px] font-bold text-text-muted tracking-tight shrink-0 whitespace-nowrap">
                    Wk {idx + 1}
                  </span>
                </div>
              );
            })}

            <div className="absolute top-2 right-3 flex items-center gap-1.5 text-[8px] font-bold text-text-muted">
              <div className="flex items-center gap-1">
                <div className="h-1.5 w-1.5 rounded-full bg-primary/20" />
                <span>Allow.</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="h-1.5 w-1.5 rounded-full bg-primary" />
                <span>Spent</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </WidgetContainer>
  );
}

export default StudentBudgetWidget;
