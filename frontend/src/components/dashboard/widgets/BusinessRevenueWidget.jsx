import React from 'react';
import { Badge } from '@/components/ui';
import * as LucideIcons from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import WidgetContainer from '../WidgetContainer';
import WidgetActions from '../WidgetActions';

export function BusinessRevenueWidget({ widget, sizeClass }) {
  const shouldReduceMotion = useReducedMotion();

  const toolbar = (
    <WidgetActions
      onInfo={() => alert('Gross revenue pipeline overview')}
      onRefresh={() => console.log('Revenue refresh')}
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
      <div className="flex flex-col gap-5 h-full select-none text-left font-sans">
        {/* Core metrics row */}
        <div className="grid grid-cols-3 gap-3 bg-muted/40 border border-border p-4 rounded-xl">
          <div className="flex flex-col text-left">
            <span className="text-[9px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Monthly Revenue
            </span>
            <span className="text-base font-extrabold text-text-primary mt-1.5">
              ₹4,85,000
            </span>
          </div>
          <div className="flex flex-col text-left border-x border-border/80 px-3">
            <span className="text-[9px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Quarterly Revenue
            </span>
            <span className="text-base font-extrabold text-text-primary mt-1.5">
              ₹14,20,000
            </span>
          </div>
          <div className="flex flex-col text-left pl-1">
            <span className="text-[9px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Annual Revenue
            </span>
            <span className="text-base font-extrabold text-text-primary mt-1.5">
              ₹55,80,000
            </span>
          </div>
        </div>

        {/* Growth and Target achievement details */}
        <div className="flex items-center justify-between text-xs font-semibold text-text-secondary">
          <div className="flex items-center gap-1">
            <LucideIcons.ArrowUpRight className="h-4 w-4 text-success" />
            <span>Target achievement status</span>
          </div>
          <Badge
            variant="secondary"
            className="text-[10px] font-bold bg-success/10 border-success/15 text-success rounded py-0.5 px-2"
          >
            92% of target reached
          </Badge>
        </div>

        {/* CSS Chart placeholder: Revenue Trend line */}
        <div className="flex flex-col gap-2 mt-auto border-t border-border/40 pt-4">
          <div className="flex justify-between items-center text-[9px] font-bold text-text-muted uppercase tracking-wider">
            <span>Revenue Trend Growth</span>
            <span>Q1-Q2 Analysis</span>
          </div>

          <div className="h-16 w-full rounded-xl bg-card border border-border/70 relative flex items-end justify-between px-6 pb-2 overflow-hidden">
            <div className="absolute inset-0 opacity-[0.02] bg-[radial-gradient(#7C3AED_1px,transparent_1px)] [background-size:10px_10px]" />
            
            {/* CSS Wave / Line representation */}
            <svg className="absolute inset-0 w-full h-full text-primary/10" preserveAspectRatio="none" viewBox="0 0 100 100">
              <path d="M0,100 L0,80 L20,70 L40,82 L60,60 L80,45 L100,20 L100,100 Z" fill="currentColor" />
              <path d="M0,80 L20,70 L40,82 L60,60 L80,45 L100,20" fill="none" stroke="var(--primary)" strokeWidth="2.5" />
            </svg>

            {/* Monthly indicators */}
            {['Apr', 'May', 'Jun', 'Jul'].map((m) => (
              <span key={m} className="text-[8px] font-bold text-text-muted z-10">{m}</span>
            ))}
          </div>
        </div>
      </div>
    </WidgetContainer>
  );
}

export default BusinessRevenueWidget;
