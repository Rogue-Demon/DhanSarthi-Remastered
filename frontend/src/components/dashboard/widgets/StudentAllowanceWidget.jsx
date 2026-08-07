import React from 'react';
import { Badge, Button } from '@/components/ui';
import * as LucideIcons from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import WidgetContainer from '../WidgetContainer';
import WidgetActions from '../WidgetActions';

export function StudentAllowanceWidget({ widget, sizeClass }) {
  const shouldReduceMotion = useReducedMotion();

  // Mock timeline activities
  const activities = [
    { text: 'Monthly allowance credited', value: '+₹5,000', icon: 'Plus', color: '#10B981', time: '1 day ago' },
    { text: 'Reference book bought', value: '-₹450', icon: 'Minus', color: '#EF4444', time: '2 days ago' },
    { text: 'Transferred to laptop savings goal', value: '-₹1,000', icon: 'ArrowRight', color: '#8B5CF6', time: '3 days ago' },
    { text: 'Logged tea/snacks expense', value: '-₹80', icon: 'Minus', color: '#EF4444', time: '3 days ago' },
  ];

  // Quick Action Buttons list
  const quickActions = [
    { label: 'Add Expense', icon: 'PlusCircle', color: '#EF4444' },
    { label: 'Add Savings', icon: 'PiggyBank', color: '#8B5CF6' },
    { label: 'View Budget', icon: 'PieChart', color: '#10B981' },
    { label: 'Create Goal', icon: 'Target', color: '#F59E0B' },
  ];

  const toolbar = (
    <WidgetActions
      onInfo={() => alert('Information on Allowance Tracking')}
      onRefresh={() => console.log('Allowance refresh')}
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
        {/* Metrics Row */}
        <div className="flex justify-between items-center bg-primary/5 border border-primary/10 p-4 rounded-2xl relative overflow-hidden">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center border border-white/40 dark:border-white/5 shadow-xs">
              <LucideIcons.Wallet className="h-5 w-5" />
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                Allowance Account
              </span>
              <span className="text-2xl font-black text-text-primary tracking-tight">
                ₹5,000
              </span>
            </div>
          </div>
          <Badge
            variant="secondary"
            className="text-[10px] font-black bg-success/15 border-success/20 text-success rounded-full py-0.5 px-2"
          >
            +10% vs last month
          </Badge>
        </div>

        {/* Activity Timeline */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <LucideIcons.History className="h-4 w-4 text-text-muted" />
            <h4 className="text-xs font-black text-text-muted uppercase tracking-wider">
              Recent Activity
            </h4>
          </div>

          <div className="flex flex-col gap-3 border-l border-border/80 ml-2.5 pl-4 relative">
            {activities.map((act, idx) => {
              const ActIcon = LucideIcons[act.icon] || LucideIcons.Circle;
              return (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, x: shouldReduceMotion ? 0 : -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  className="flex items-start justify-between relative group"
                >
                  {/* Timeline dot */}
                  <div
                    className="absolute left-[-21.5px] top-[4px] h-3.5 w-3.5 rounded-full border-2 border-card flex items-center justify-center text-white"
                    style={{ background: act.color }}
                  >
                    <ActIcon className="h-1.5 w-1.5 stroke-[3px]" />
                  </div>

                  <div className="flex flex-col gap-0.5">
                    <span className="text-xs font-extrabold text-text-primary group-hover:text-primary transition-colors duration-200">
                      {act.text}
                    </span>
                    <span className="text-[10px] font-bold text-text-muted">
                      {act.time}
                    </span>
                  </div>
                  <span
                    className="text-xs font-black"
                    style={{ color: act.value.startsWith('+') ? '#10B981' : 'var(--text-primary)' }}
                  >
                    {act.value}
                  </span>
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* Quick Action Button Strip */}
        <div className="flex flex-col gap-2.5 border-t border-border/50 pt-4 mt-auto">
          <h4 className="text-xs font-black text-text-muted uppercase tracking-wider">
            Quick Actions
          </h4>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {quickActions.map((btn) => {
              const Icon = LucideIcons[btn.icon] || LucideIcons.Settings;
              return (
                <Button
                  key={btn.label}
                  variant="secondary"
                  size="sm"
                  className="rounded-xl border border-border/70 hover:border-primary/20 shadow-xs flex flex-col items-center justify-center p-2.5 gap-1.5 text-[10px] font-black uppercase text-text-secondary h-auto bg-card"
                  onClick={() => alert(`Quick action: ${btn.label}`)}
                >
                  <div
                    className="p-1.5 rounded-lg flex items-center justify-center text-white"
                    style={{ background: btn.color }}
                  >
                    <Icon className="h-4 w-4" />
                  </div>
                  <span>{btn.label}</span>
                </Button>
              );
            })}
          </div>
        </div>
      </div>
    </WidgetContainer>
  );
}

export default StudentAllowanceWidget;
