import React from 'react';
import { Badge } from '@/components/ui';
import * as LucideIcons from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import WidgetContainer from '../WidgetContainer';
import WidgetActions from '../WidgetActions';

export function BusinessPayrollWidget({ widget, sizeClass }) {
  const shouldReduceMotion = useReducedMotion();

  // Mock activity timelines
  const activities = [
    { text: 'Invoice #INV-081 generated', type: 'billing', time: '2 hours ago', icon: 'FileSpreadsheet' },
    { text: 'Monthly payroll processed successfully', type: 'payroll', time: '1 day ago', icon: 'Users' },
    { text: 'Server hosting expense logged', type: 'expense', time: '2 days ago', icon: 'Database' },
    { text: 'Raw inventory restock purchase order', type: 'inventory', time: '3 days ago', icon: 'ShoppingCart' },
  ];

  const toolbar = (
    <WidgetActions
      onInfo={() => alert('Corporate payroll and historical activity events')}
      onRefresh={() => console.log('Payroll refresh')}
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
              Active Monthly Payroll (12 Employees)
            </span>
            <span className="text-3xl font-extrabold text-text-primary tracking-tight mt-1.5">
              ₹95,000
            </span>
            <span className="text-xs text-text-secondary mt-1 font-medium">
              Next credit cycle scheduled on 31st Aug
            </span>
          </div>
          <Badge
            variant="secondary"
            className="text-[10px] font-bold bg-success/10 border-success/15 text-success py-0.5 px-2 rounded"
          >
            Processed
          </Badge>
        </div>

        {/* Corporate Activity Timeline */}
        <div className="flex flex-col gap-3">
          <span className="text-[9px] font-bold text-text-muted uppercase tracking-wider leading-none">
            Corporate Operations Timeline
          </span>

          <div className="flex flex-col gap-3 border-l border-border/80 ml-2 pl-4 relative">
            {activities.slice(0, 3).map((act, idx) => {
              const Icon = LucideIcons[act.icon] || LucideIcons.Info;
              return (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, x: shouldReduceMotion ? 0 : -5 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  className="flex justify-between items-center text-xs relative group"
                >
                  {/* Dot overlay */}
                  <div className="absolute left-[-21.5px] top-[4px] h-3.5 w-3.5 rounded-full border-2 border-card bg-primary flex items-center justify-center text-white">
                    <Icon className="h-1.5 w-1.5 stroke-[2.5]" />
                  </div>

                  <div className="flex flex-col gap-0.5 text-left pl-1">
                    <span className="font-extrabold text-text-primary group-hover:text-primary transition-colors duration-200">{act.text}</span>
                    <span className="text-[10px] font-bold text-text-muted">{act.time}</span>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </WidgetContainer>
  );
}

export default BusinessPayrollWidget;
