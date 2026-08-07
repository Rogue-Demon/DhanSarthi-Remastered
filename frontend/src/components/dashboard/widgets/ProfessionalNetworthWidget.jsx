import React from 'react';
import { Badge } from '@/components/ui';
import * as LucideIcons from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import WidgetContainer from '../WidgetContainer';
import WidgetActions from '../WidgetActions';

export function ProfessionalNetworthWidget({ widget, sizeClass }) {
  const shouldReduceMotion = useReducedMotion();

  const toolbar = (
    <WidgetActions
      onInfo={() => alert('Net Worth calculation and financial health score')}
      onRefresh={() => console.log('Networth refresh')}
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
        {/* Core Metric */}
        <div className="flex justify-between items-start">
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Estimated Net Worth
            </span>
            <span className="text-3xl font-extrabold text-text-primary tracking-tight mt-1.5">
              ₹7,25,000
            </span>
            <span className="text-xs text-text-secondary mt-1 font-medium flex items-center gap-1">
              <LucideIcons.ArrowUpRight className="h-3.5 w-3.5 text-success" />
              <span>+₹32,450 this month</span>
            </span>
          </div>
          <Badge
            variant="secondary"
            className="text-[10px] font-bold bg-success/10 border-success/15 text-success py-0.5 px-2 rounded"
          >
            Growing
          </Badge>
        </div>

        {/* Assets vs Liabilities Breakdown */}
        <div className="grid grid-cols-2 gap-4 bg-muted/30 border border-border/80 p-3 rounded-xl text-xs">
          <div className="flex flex-col text-left pl-2 border-l-2 border-success">
            <span className="font-bold text-text-muted">Total Assets</span>
            <span className="text-sm font-extrabold text-text-primary mt-1">₹8,45,000</span>
          </div>
          <div className="flex flex-col text-left pl-2 border-l-2 border-danger">
            <span className="font-bold text-text-muted">Total Liabilities</span>
            <span className="text-sm font-extrabold text-text-primary mt-1">₹1,20,000</span>
          </div>
        </div>

        {/* Financial Health Score (Executive look) */}
        <div className="flex items-center gap-4 mt-auto border-t border-border/40 pt-4">
          {/* Minimal health score progress ring */}
          <div className="relative h-12 w-12 flex items-center justify-center shrink-0">
            <svg className="h-full w-full transform -rotate-90" viewBox="0 0 36 36">
              <path
                className="text-muted"
                strokeWidth="3"
                stroke="currentColor"
                fill="transparent"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                className="text-primary transition-all duration-500"
                strokeWidth="3"
                strokeDasharray="78, 100"
                strokeLinecap="round"
                stroke="currentColor"
                fill="transparent"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>
            <span className="absolute text-[10px] font-black text-text-primary">78%</span>
          </div>

          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-extrabold text-text-primary">Financial Health Score</span>
              <Badge variant="secondary" className="text-[8px] font-bold py-0 px-1 bg-primary/10 border-primary/20 text-primary">Stable</Badge>
            </div>
            <span className="text-[10px] font-bold text-text-muted mt-0.5 leading-tight">
              Deductions optimization can increase score to 85%
            </span>
          </div>
        </div>
      </div>
    </WidgetContainer>
  );
}

export default ProfessionalNetworthWidget;
