import React from 'react';
import { Badge } from '@/components/ui';
import * as LucideIcons from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import WidgetContainer from '../WidgetContainer';
import WidgetActions from '../WidgetActions';

export function StudentEducationWidget({ widget, sizeClass }) {
  const shouldReduceMotion = useReducedMotion();

  // Mock reminders list
  const reminders = [
    { title: 'Scholarship Application', desc: 'National Merit Fellowship submission', due: '15th Aug', color: '#10B981' },
    { title: 'Semester Exam Fees', desc: 'University online billing portal link', due: '20th Aug', color: '#EF4444' },
    { title: 'Monthly Savings deposit', desc: 'Laptop target automated transfer', due: '25th Aug', color: '#8B5CF6' },
  ];

  const toolbar = (
    <WidgetActions
      onInfo={() => alert('Information on Education Expenses')}
      onRefresh={() => console.log('Education refresh')}
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
        <div className="flex justify-between items-center bg-info/5 border border-info/10 p-4 rounded-2xl relative overflow-hidden">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-info/10 text-info flex items-center justify-center border border-white/40 dark:border-white/5 shadow-xs">
              <LucideIcons.GraduationCap className="h-5 w-5" />
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                Education Spend
              </span>
              <span className="text-2xl font-black text-text-primary tracking-tight">
                ₹3,500
              </span>
            </div>
          </div>
          <Badge
            variant="secondary"
            className="text-[10px] font-black bg-info/10 border-info/25 text-info rounded-full py-0.5 px-2"
          >
            -5% this month
          </Badge>
        </div>

        {/* Upcoming Reminders List */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <LucideIcons.Bell className="h-4 w-4 text-text-muted animate-bounce" />
            <h4 className="text-xs font-black text-text-muted uppercase tracking-wider">
              Upcoming Reminders
            </h4>
          </div>

          <div className="flex flex-col gap-2.5">
            {reminders.map((rem, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 5 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="flex items-center justify-between p-3 rounded-xl bg-muted/50 border border-border/80 shadow-xs relative overflow-hidden group hover:border-primary/20 transition-all duration-200"
              >
                <div
                  className="absolute left-0 top-0 bottom-0 w-1"
                  style={{ background: rem.color }}
                />
                <div className="flex flex-col text-left gap-0.5 pl-1.5">
                  <span className="text-xs font-extrabold text-text-primary">
                    {rem.title}
                  </span>
                  <span className="text-[10px] font-bold text-text-muted truncate max-w-[160px] sm:max-w-xs">
                    {rem.desc}
                  </span>
                </div>
                <div className="flex flex-col items-end shrink-0">
                  <span className="text-[9px] font-black text-text-muted uppercase tracking-wider leading-none">
                    Due By
                  </span>
                  <span className="text-xs font-black text-text-secondary mt-0.5">
                    {rem.due}
                  </span>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Expense Breakdown CSS Donut Chart Placeholder */}
        <div className="flex flex-col gap-2.5 border-t border-border/50 pt-4 mt-auto">
          <h4 className="text-xs font-black text-text-muted uppercase tracking-wider">
            Education Spend Categories
          </h4>
          <div className="flex items-center justify-between bg-card border border-border/70 p-3 rounded-2xl gap-4">
            {/* Mock Donut Chart using Tailwind ring utilities and gradients */}
            <div className="relative h-16 w-16 flex items-center justify-center shrink-0">
              <div className="absolute inset-0 rounded-full border-[8px] border-muted" />
              {/* Themed segment colors overlays */}
              <div className="absolute inset-0 rounded-full border-[8px] border-transparent border-t-info border-r-info rotate-45" />
              <div className="absolute inset-0 rounded-full border-[8px] border-transparent border-b-accent rotate-[-45deg]" />
              <div className="h-7 w-7 rounded-full bg-card shadow-inner flex items-center justify-center text-[9px] font-black text-text-muted">
                60%
              </div>
            </div>

            {/* Donut Legend */}
            <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 flex-1 text-left">
              <div className="flex items-center gap-1.5">
                <div className="h-2 w-2 rounded-full bg-info shrink-0" />
                <span className="text-[10px] font-bold text-text-secondary">Fees (60%)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="h-2 w-2 rounded-full bg-accent shrink-0" />
                <span className="text-[10px] font-bold text-text-secondary">Books (30%)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="h-2 w-2 rounded-full bg-primary shrink-0" />
                <span className="text-[10px] font-bold text-text-secondary">Subs (10%)</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </WidgetContainer>
  );
}

export default StudentEducationWidget;
