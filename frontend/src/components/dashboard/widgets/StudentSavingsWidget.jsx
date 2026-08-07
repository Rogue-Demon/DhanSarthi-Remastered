import React from 'react';
import { Badge } from '@/components/ui';
import * as LucideIcons from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import WidgetContainer from '../WidgetContainer';
import WidgetActions from '../WidgetActions';

export function StudentSavingsWidget({ widget, sizeClass }) {
  const shouldReduceMotion = useReducedMotion();

  const toolbar = (
    <WidgetActions
      onInfo={() => alert('Information on Savings Goals')}
      onRefresh={() => console.log('Savings refresh')}
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
        {/* Metrics Header */}
        <div className="flex justify-between items-center bg-accent/5 border border-accent/10 p-4 rounded-2xl relative overflow-hidden">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-accent/10 text-accent flex items-center justify-center border border-white/40 dark:border-white/5 shadow-xs">
              <LucideIcons.PiggyBank className="h-5 w-5" />
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                Total Savings
              </span>
              <span className="text-2xl font-black text-text-primary tracking-tight">
                ₹12,450
              </span>
            </div>
          </div>
          <Badge
            variant="secondary"
            className="text-[10px] font-black bg-accent/10 border-accent/25 text-accent rounded-full py-0.5 px-2"
          >
            +15% saving rate
          </Badge>
        </div>

        {/* Savings Streak Widget Section */}
        <div className="clay-surface bg-muted/20 border border-border p-4 rounded-2xl flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 rounded-full bg-warning/15 flex items-center justify-center text-warning shadow-sm border border-white/50 relative">
              <LucideIcons.Flame className="h-6 w-6 stroke-[2.2] animate-pulse" />
              <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-danger text-[8px] font-black text-white">
                🔥
              </span>
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-1.5">
                <span className="text-sm font-black text-text-primary leading-none">
                  14-Day Streak
                </span>
                <Badge variant="secondary" className="text-[8px] font-black uppercase tracking-wider py-0 px-1 bg-warning/10 text-warning border-warning/15">
                  Saver Streak
                </Badge>
              </div>
              <span className="text-[11px] font-bold text-text-secondary mt-1">
                "Amazing! You're saving ₹200 daily."
              </span>
            </div>
          </div>
          
          {/* Streak Stats */}
          <div className="flex flex-col text-right shrink-0">
            <span className="text-[9px] font-black text-text-muted uppercase tracking-wider leading-none">
              Longest
            </span>
            <span className="text-sm font-black text-text-secondary">
              21 Days
            </span>
          </div>
        </div>

        {/* Beautiful CSS Chart Placeholder: Savings Growth Wave */}
        <div className="flex flex-col gap-2.5 border-t border-border/50 pt-4 mt-auto">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-black text-text-muted uppercase tracking-wider">
              Savings Growth History
            </h4>
            <span className="text-[9px] font-black text-text-muted uppercase tracking-wider">
              Last 5 months
            </span>
          </div>

          {/* Mock wave chart */}
          <div className="h-20 w-full rounded-2xl bg-card border border-border/70 relative flex items-end px-4 py-2 overflow-hidden">
            <div className="absolute inset-0 opacity-[0.02] bg-[radial-gradient(#7C3AED_1px,transparent_1px)] [background-size:8px_8px]" />
            
            {/* CSS Chart curve paths using stylized gradient overlays */}
            <div className="absolute inset-x-0 bottom-0 h-10 bg-gradient-to-t from-accent/5 to-transparent pointer-events-none" />
            <svg className="absolute inset-0 w-full h-full text-accent/20" preserveAspectRatio="none" viewBox="0 0 100 100">
              <path
                d="M0,100 C15,85 30,65 50,75 C70,85 85,45 100,25 L100,100 Z"
                fill="currentColor"
              />
              <path
                d="M0,100 C15,85 30,65 50,75 C70,85 85,45 100,25"
                fill="none"
                stroke="var(--accent)"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
            </svg>

            {/* Metric value pills over chart */}
            <div className="absolute top-2 left-3 flex gap-2">
              <span className="text-[9px] font-bold bg-muted px-1.5 py-0.5 rounded text-text-secondary border border-border">Mar: ₹4k</span>
              <span className="text-[9px] font-bold bg-muted px-1.5 py-0.5 rounded text-text-secondary border border-border">Jul: ₹12k</span>
            </div>

            <div className="absolute bottom-2 right-3 flex items-center gap-1 text-[9px] font-black text-accent uppercase tracking-wider">
              <LucideIcons.Sparkles className="h-2.5 w-2.5" />
              <span>Projected to reach target soon</span>
            </div>
          </div>
        </div>
      </div>
    </WidgetContainer>
  );
}

export default StudentSavingsWidget;
