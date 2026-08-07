import React from 'react';
import { Badge } from '@/components/ui';
import * as LucideIcons from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import WidgetContainer from '../WidgetContainer';
import WidgetActions from '../WidgetActions';

export function BusinessProfitWidget({ widget, sizeClass }) {
  const shouldReduceMotion = useReducedMotion();

  // Mock insights list
  const insights = [
    { text: 'Operating expenses increased by 3.2% MoM.', icon: 'ArrowUpRight', color: '#EF4444' },
    { text: 'Revenue growth remains positive for the 3rd consecutive quarter.', icon: 'CheckCircle', color: '#10B981' },
    { text: 'Outstanding invoices require immediate credit checks.', icon: 'AlertCircle', color: '#F59E0B' },
  ];

  const toolbar = (
    <WidgetActions
      onInfo={() => alert('Operating margins and business health status')}
      onRefresh={() => console.log('Profit refresh')}
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
        {/* Core Metric & Margin Info */}
        <div className="flex justify-between items-start">
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Net Profit Margin (OPEX subtracted)
            </span>
            <span className="text-3xl font-extrabold text-text-primary tracking-tight mt-1.5">
              ₹1,45,000
            </span>
            <span className="text-xs text-text-secondary mt-1 font-medium">
              30% average net profit ratio
            </span>
          </div>
          <Badge
            variant="secondary"
            className="text-[10px] font-bold bg-primary/10 border-primary/20 text-primary py-0.5 px-2 rounded"
          >
            Optimal
          </Badge>
        </div>

        {/* Business Health Score & AI Smart Insights row */}
        <div className="flex items-center gap-4 bg-muted/30 border border-border/80 p-3.5 rounded-xl">
          {/* Health circular progress */}
          <div className="relative h-12 w-12 flex items-center justify-center shrink-0">
            <svg className="h-full w-full transform -rotate-90" viewBox="0 0 36 36">
              <path
                className="text-muted"
                strokeWidth="3.2"
                stroke="currentColor"
                fill="transparent"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                className="text-primary transition-all duration-500"
                strokeWidth="3.2"
                strokeDasharray="84, 100"
                strokeLinecap="round"
                stroke="currentColor"
                fill="transparent"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>
            <span className="absolute text-[10px] font-black text-text-primary">84%</span>
          </div>

          <div className="flex flex-col text-left">
            <span className="text-xs font-extrabold text-text-primary leading-none">Business Health Index</span>
            <span className="text-[10px] font-bold text-text-muted mt-1 leading-tight">
              Calculated from current liquid reserves vs operating overheads.
            </span>
          </div>
        </div>

        {/* Insights list */}
        <div className="flex flex-col gap-2 mt-auto border-t border-border/40 pt-4">
          <span className="text-[9px] font-bold text-text-muted uppercase tracking-wider leading-none">
            Corporate Insights
          </span>
          
          <div className="flex flex-col gap-2">
            {insights.map((ins, idx) => {
              const Icon = LucideIcons[ins.icon] || LucideIcons.Info;
              return (
                <div key={idx} className="flex items-start gap-2.5 text-xs text-text-secondary">
                  <Icon className="h-3.5 w-3.5 shrink-0 mt-0.5" style={{ color: ins.color }} />
                  <span className="font-semibold leading-normal">{ins.text}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </WidgetContainer>
  );
}

export default BusinessProfitWidget;
