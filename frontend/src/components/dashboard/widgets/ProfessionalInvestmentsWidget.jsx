import React from 'react';
import { Badge, Button } from '@/components/ui';
import * as LucideIcons from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import WidgetContainer from '../WidgetContainer';
import WidgetActions from '../WidgetActions';

export function ProfessionalInvestmentsWidget({ widget, sizeClass }) {
  const shouldReduceMotion = useReducedMotion();

  // Mock allocation items
  const allocation = [
    { name: 'Mutual Funds', value: '₹1,40,400', share: '45%', color: '#7C3AED' },
    { name: 'Direct Equity (Stocks)', value: '₹1,09,200', share: '35%', color: '#3B82F6' },
    { name: 'Fixed Deposits (FD)', value: '₹31,200', share: '10%', color: '#10B981' },
    { name: 'Sovereign Gold (SGB)', value: '₹31,200', share: '10%', color: '#F59E0B' },
  ];

  const toolbar = (
    <WidgetActions
      onInfo={() => alert('Investment portfolio allocation and tax liabilities')}
      onRefresh={() => console.log('Investments refresh')}
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
        
        {/* COLUMN 1: PORTFOLIO ALLOCATION (60% width) */}
        <div className="flex-1 lg:flex-[1.2] flex flex-col gap-4">
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Portfolio Assets Valuation
            </span>
            <div className="flex items-baseline gap-2.5 mt-1.5">
              <span className="text-2xl font-extrabold text-text-primary tracking-tight">
                ₹3,12,000
              </span>
              <span className="text-xs font-bold text-success flex items-center gap-0.5">
                <LucideIcons.ArrowUpRight className="h-3 w-3 stroke-[2.5]" />
                <span>+1.34% today</span>
              </span>
            </div>
          </div>

          {/* Allocation details table list */}
          <div className="flex flex-col gap-2.5">
            <span className="text-[9px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Asset Allocation Mappings
            </span>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {allocation.map((item, idx) => (
                <div
                  key={item.name}
                  className="flex items-center justify-between p-2 rounded-lg bg-muted/40 border border-border/80 text-xs font-semibold text-text-secondary hover:border-primary/20 transition-all duration-200"
                >
                  <div className="flex items-center gap-2 text-left">
                    <div className="h-2 w-2 rounded-full shrink-0" style={{ backgroundColor: item.color }} />
                    <span className="truncate max-w-[90px]">{item.name}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="font-extrabold text-text-primary">{item.value}</span>
                    <span className="text-[10px] font-bold text-text-muted">{item.share}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* COLUMN 2: TAX OVERVIEW & DEDUCTIONS (40% width) */}
        <div className="flex-1 border-t lg:border-t-0 lg:border-l border-border/60 pt-4 lg:pt-0 lg:pl-6 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <LucideIcons.Percent className="h-4 w-4 text-primary" />
              <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">
                Tax liability (FY 2026-27)
              </span>
            </div>
            <Badge variant="secondary" className="text-[8px] font-bold py-0.5 px-1.5 bg-primary/10 border-primary/20 text-primary">
              Section 80C Optimized
            </Badge>
          </div>

          {/* Tax values */}
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between text-xs font-semibold text-text-secondary">
              <span>Estimated Tax Liability</span>
              <span className="font-extrabold text-text-primary">₹34,500</span>
            </div>
            <div className="flex items-center justify-between text-xs font-semibold text-text-secondary border-t border-border/40 pt-2">
              <span>Tax Saved via Deductions</span>
              <span className="font-extrabold text-success">₹15,000</span>
            </div>
            <div className="flex items-center justify-between text-xs font-semibold text-text-secondary border-t border-border/40 pt-2">
              <span>Upcoming Tax Filing Due</span>
              <span className="font-extrabold text-text-primary">31st Jul 2027</span>
            </div>
          </div>

          <Button
            variant="ghost"
            size="xs"
            className="w-full justify-center border border-border/80 bg-muted/20 hover:bg-muted/40 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-wider text-text-secondary mt-auto"
            onClick={() => alert('Tax optimization analyzer tool')}
            iconRight={<LucideIcons.ExternalLink className="h-3 w-3" />}
          >
            Optimize Deductions
          </Button>
        </div>

      </div>
    </WidgetContainer>
  );
}

export default ProfessionalInvestmentsWidget;
