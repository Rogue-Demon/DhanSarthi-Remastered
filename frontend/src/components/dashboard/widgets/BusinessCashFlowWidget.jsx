import React from 'react';
import { Badge, Button } from '@/components/ui';
import * as LucideIcons from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import WidgetContainer from '../WidgetContainer';
import WidgetActions from '../WidgetActions';

export function BusinessCashFlowWidget({ widget, sizeClass }) {
  const shouldReduceMotion = useReducedMotion();

  // Receivables list
  const receivables = [
    { client: 'Acme Corp Inc.', amount: '₹45,000', invoice: '#INV-2026-081', status: 'overdue', color: '#EF4444' },
    { client: 'Globex Logistics', amount: '₹72,000', invoice: '#INV-2026-094', status: 'pending', color: '#F59E0B' },
  ];

  // Payables list
  const payables = [
    { vendor: 'Amazon Cloud Web', amount: '₹14,500', due: '12th Aug', type: 'SaaS Bill' },
    { vendor: 'Vertex Office Rental', amount: '₹35,000', due: '10th Aug', type: 'Office Rent' },
  ];

  const toolbar = (
    <WidgetActions
      onInfo={() => alert('Corporate liquidity cash flow details')}
      onRefresh={() => console.log('Cash flow refresh')}
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
      <div className="flex flex-col lg:flex-row gap-8 w-full select-none text-left font-sans">
        
        {/* COLUMN 1: STATEMENT METRICS (35% width) */}
        <div className="flex-1 lg:flex-[1.2] flex flex-col gap-4">
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Net cash flow statement
            </span>
            <div className="flex items-baseline gap-2 mt-1.5">
              <span className="text-2xl font-extrabold text-text-primary tracking-tight">
                +₹2,10,000
              </span>
              <Badge variant="secondary" className="text-[8px] font-bold py-0.5 px-1.5 bg-success/10 border-success/20 text-success rounded ml-2">
                Positive flow
              </Badge>
            </div>
          </div>

          <div className="flex flex-col gap-2.5 bg-muted/40 border border-border p-3.5 rounded-xl text-xs font-semibold text-text-secondary">
            <div className="flex justify-between">
              <span>Money In (Invoices collected)</span>
              <span className="font-extrabold text-success">₹4,85,000</span>
            </div>
            <div className="flex justify-between border-t border-border/40 pt-2.5">
              <span>Money Out (Operational costs)</span>
              <span className="font-extrabold text-danger">₹2,75,000</span>
            </div>
          </div>
        </div>

        {/* COLUMN 2: PENDING RECEIVABLES / INVOICES (35% width) */}
        <div className="flex-1 lg:flex-[1.3] border-t lg:border-t-0 lg:border-x border-border/60 pt-4 lg:pt-0 lg:px-6 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider leading-none">
              Pending Receivables
            </span>
            <span className="text-[10px] font-black text-text-muted">Overdue: ₹45,000</span>
          </div>

          <div className="flex flex-col gap-2">
            {receivables.map((inv, idx) => (
              <div key={idx} className="flex justify-between items-center bg-muted/30 border border-border/50 p-2.5 rounded-lg text-xs font-semibold">
                <div className="flex flex-col text-left border-l-2 pl-2" style={{ borderColor: inv.color }}>
                  <span className="font-extrabold text-text-primary">{inv.client}</span>
                  <span className="text-[10px] font-bold text-text-muted">{inv.invoice}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="font-extrabold text-text-primary">{inv.amount}</span>
                  <Badge variant="secondary" className="text-[8px] font-bold py-0.5 px-1 bg-muted border border-border text-text-muted capitalize">
                    {inv.status}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* COLUMN 3: VENDOR PAYABLES (30% width) */}
        <div className="flex-1 border-t lg:border-t-0 pt-4 lg:pt-0 flex flex-col gap-3">
          <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider leading-none">
            Upcoming Payables
          </span>

          <div className="flex flex-col gap-2">
            {payables.map((bill, idx) => (
              <div key={idx} className="flex justify-between items-center bg-muted/30 border border-border/50 p-2.5 rounded-lg text-xs font-semibold">
                <div className="flex flex-col text-left">
                  <span className="font-extrabold text-text-primary">{bill.vendor}</span>
                  <span className="text-[10px] font-bold text-text-muted">{bill.type}</span>
                </div>
                <div className="flex flex-col items-end">
                  <span className="font-extrabold text-text-primary">{bill.amount}</span>
                  <span className="text-[9px] font-bold text-danger leading-none mt-1">{bill.due}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </WidgetContainer>
  );
}

export default BusinessCashFlowWidget;
