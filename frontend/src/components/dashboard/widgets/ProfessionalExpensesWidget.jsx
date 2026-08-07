import React from 'react';
import { Badge } from '@/components/ui';
import * as LucideIcons from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import WidgetContainer from '../WidgetContainer';
import WidgetActions from '../WidgetActions';

export function ProfessionalExpensesWidget({ widget, sizeClass }) {
  const shouldReduceMotion = useReducedMotion();

  // Mock bills list
  const bills = [
    { title: 'Apartment Rent EMI', amount: '₹18,000', due: 'Due 10th Aug', status: 'pending', color: '#EF4444' },
    { title: 'Premium Health Insurance', amount: '₹4,500', due: 'Paid 3rd Aug', status: 'paid', color: '#10B981' },
    { title: 'Credit Card Statement', amount: '₹12,200', due: 'Due 15th Aug', status: 'pending', color: '#EF4444' },
  ];

  const toolbar = (
    <WidgetActions
      onInfo={() => alert('Expense details and monthly bill cycles')}
      onRefresh={() => console.log('Expenses refresh')}
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
              Accumulated Monthly Expenses
            </span>
            <span className="text-3xl font-extrabold text-text-primary tracking-tight mt-1.5">
              ₹42,750
            </span>
            <span className="text-xs text-text-secondary mt-1 font-medium">
              64% of total monthly budget spent
            </span>
          </div>
          <Badge
            variant="secondary"
            className="text-[10px] font-bold bg-danger/10 border-danger/15 text-danger py-0.5 px-2 rounded"
          >
            +4.8% MoM
          </Badge>
        </div>

        {/* Bill Reminders List */}
        <div className="flex flex-col gap-2.5">
          <span className="text-[9px] font-bold text-text-muted uppercase tracking-wider leading-none">
            Upcoming Bills & EMIs
          </span>

          <div className="flex flex-col gap-2">
            {bills.map((bill, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 5 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="flex items-center justify-between p-2.5 rounded-lg bg-muted/40 border border-border/80 text-xs font-semibold text-text-secondary hover:border-primary/20 transition-all duration-200"
              >
                <div className="flex flex-col gap-0.5 text-left border-l-2 pl-2" style={{ borderColor: bill.color }}>
                  <span className="font-extrabold text-text-primary">{bill.title}</span>
                  <span className="text-[10px] font-bold text-text-muted">{bill.due}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-extrabold text-text-primary">{bill.amount}</span>
                  <div
                    className="h-2 w-2 rounded-full shrink-0"
                    style={{ backgroundColor: bill.status === 'paid' ? '#10B981' : '#EF4444' }}
                  />
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Recent Transactions List */}
        <div className="flex flex-col gap-2 mt-auto border-t border-border/40 pt-4">
          <span className="text-[9px] font-bold text-text-muted uppercase tracking-wider leading-none">
            Recent Transactions
          </span>
          <div className="flex justify-between items-center text-xs">
            <div className="flex items-center gap-2">
              <div className="p-1 rounded bg-muted text-text-muted">
                <LucideIcons.ShoppingBag className="h-3.5 w-3.5" />
              </div>
              <span className="font-bold text-text-secondary">Groceries Expense</span>
            </div>
            <span className="font-extrabold text-text-primary">-₹3,420</span>
          </div>
        </div>
      </div>
    </WidgetContainer>
  );
}

export default ProfessionalExpensesWidget;
