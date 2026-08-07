import React from 'react';
import { Badge, Button } from '@/components/ui';
import * as LucideIcons from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import WidgetContainer from '../WidgetContainer';
import WidgetActions from '../WidgetActions';

export function ProfessionalAssetsWidget({ widget, sizeClass }) {
  const shouldReduceMotion = useReducedMotion();

  // Mock savings goals
  const goals = [
    { title: 'Emergency Fund (6M expenses)', current: 120000, target: 150000, progress: 80, due: 'Oct 2026', color: '#10B981' },
    { title: 'Home Down Payment', current: 400000, target: 1000000, progress: 40, due: 'Dec 2028', color: '#7C3AED' },
  ];

  // Mock Calendar events
  const calendar = [
    { event: 'Rent & Bills Debit', day: '10th', type: 'recurring' },
    { event: 'Mutual Fund SIP Date', day: '05th', type: 'investment' },
    { event: 'Credit Card Pay Date', day: '15th', type: 'payment' },
  ];

  // Mock AI Insights
  const insights = [
    { text: 'You are saving 22% of your monthly net salary.', icon: 'CheckCircle', color: '#10B981' },
    { text: 'Emergency fund is 80% complete. Keep it up!', icon: 'TrendingUp', color: '#7C3AED' },
    { text: 'Utility charges increased by 12% MoM.', icon: 'AlertCircle', color: '#EF4444' },
  ];

  const toolbar = (
    <WidgetActions
      onInfo={() => alert('Long-term savings goals and payment events')}
      onRefresh={() => console.log('Assets/goals refresh')}
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
      <div className="flex flex-col lg:flex-row gap-6 w-full select-none text-left font-sans">
        
        {/* COLUMN 1: GOALS & PROGRESS (60% width) */}
        <div className="flex-1 lg:flex-[1.2] flex flex-col gap-4">
          <div className="flex justify-between items-center">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Long-term Savings Goals
            </span>
            <Button
              variant="ghost"
              size="xs"
              className="p-0 text-[10px] font-bold text-primary hover:bg-transparent uppercase tracking-wider"
              onClick={() => alert('Goal creation form')}
              iconLeft={<LucideIcons.Plus className="h-3 w-3" />}
            >
              Add Goal
            </Button>
          </div>

          {/* Goal progress cards */}
          <div className="flex flex-col gap-3">
            {goals.map((goal, idx) => (
              <div
                key={goal.title}
                className="clay-surface bg-card border border-border/80 p-3.5 flex flex-col gap-2.5 shadow-card hover:border-primary/20 transition-all duration-200"
              >
                <div className="flex items-center justify-between text-xs font-bold text-text-primary">
                  <span className="truncate max-w-[150px] sm:max-w-xs">{goal.title}</span>
                  <span className="text-[10px] font-black text-text-muted">Target: {goal.due}</span>
                </div>

                {/* Progress bar */}
                <div className="flex items-center gap-3">
                  <div className="flex-1 bg-muted h-2.5 rounded-full overflow-hidden border border-white/60 shadow-inner relative">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{ width: `${goal.progress}%`, backgroundColor: goal.color }}
                    />
                  </div>
                  <span className="text-[10px] font-black text-text-primary shrink-0 leading-none">
                    {goal.progress}%
                  </span>
                </div>

                <div className="flex justify-between items-center text-[9px] font-bold text-text-muted uppercase tracking-wider">
                  <span>Current: ₹{goal.current.toLocaleString()}</span>
                  <span>Target: ₹{goal.target.toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* COLUMN 2: FINANCIAL CALENDAR & AI ADVISOR INSIGHTS (40% width) */}
        <div className="flex-1 border-t lg:border-t-0 lg:border-l border-border/60 pt-4 lg:pt-0 lg:pl-6 flex flex-col gap-4">
          <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider leading-none">
            Schedule & Smart Insights
          </span>

          {/* Mini Calendar list */}
          <div className="flex flex-col gap-2">
            {calendar.slice(0, 2).map((item, idx) => (
              <div key={idx} className="flex items-center justify-between text-xs font-semibold text-text-secondary bg-muted/30 p-2 rounded-lg border border-border/50">
                <span className="truncate max-w-[120px]">{item.event}</span>
                <span className="font-extrabold text-primary bg-primary/5 border border-primary/10 py-0.5 px-2 rounded-md">{item.day} Monthly</span>
              </div>
            ))}
          </div>

          {/* Smart Insights list */}
          <div className="flex flex-col gap-2.5 mt-auto">
            {insights.slice(0, 2).map((ins, idx) => {
              const InsIcon = LucideIcons[ins.icon] || LucideIcons.Sparkles;
              return (
                <div key={idx} className="p-2.5 rounded-xl bg-primary/5 border border-primary/10 flex gap-2.5 items-start">
                  <div className="h-4.5 w-4.5 rounded-full bg-primary/10 flex items-center justify-center shrink-0 text-primary mt-0.5">
                    <InsIcon className="h-3.5 w-3.5" />
                  </div>
                  <p className="text-[10px] font-bold text-text-secondary leading-normal">
                    {ins.text}
                  </p>
                </div>
              );
            })}
          </div>
        </div>

      </div>
    </WidgetContainer>
  );
}

export default ProfessionalAssetsWidget;
