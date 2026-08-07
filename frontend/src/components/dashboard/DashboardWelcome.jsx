import React from 'react';
import { useProfile } from '@/hooks';
import * as LucideIcons from 'lucide-react';
import { cn } from '@/utils';

/**
 * DashboardWelcome Component
 *
 * Renders a lightweight getting-started guide card (welcome widget checklist)
 * customized to the active profile's goals.
 */
export function DashboardWelcome({ className, ...props }) {
  const { profile, profileConfig } = useProfile();

  if (!profileConfig) return null;

  // Custom onboarding setup instructions list based on profile
  const getTasks = () => {
    switch (profile) {
      case 'Student':
        return [
          { text: 'Set up weekly pocket money allowance', completed: true },
          { text: 'Create education budget category', completed: false },
          { text: 'Link student scholarship source', completed: false },
        ];
      case 'Working Professional':
        return [
          { text: 'Define monthly salary credit day', completed: true },
          { text: 'Map recurring investments & SIPs', completed: false },
          { text: 'Set threshold limit for expenses', completed: false },
        ];
      case 'Business':
        return [
          { text: 'Configure gross monthly revenue source', completed: true },
          { text: 'Verify outstanding client invoices', completed: false },
          { text: 'Link operational opex budget accounts', completed: false },
        ];
      default:
        return [];
    }
  };

  const tasks = getTasks();

  return (
    <div
      className={cn(
        'clay-surface bg-card p-5 border border-white/60 dark:border-white/5 shadow-card flex flex-col justify-between min-h-[220px] select-none text-left relative overflow-hidden',
        className
      )}
      {...props}
    >
      {/* Decorative gradient overlay */}
      <div
        className="absolute top-0 right-0 w-24 h-24 rounded-full blur-2xl opacity-[0.08]"
        style={{ background: profileConfig.gradient }}
      />

      <div className="flex flex-col gap-3">
        {/* Header */}
        <div className="flex items-center gap-2">
          <LucideIcons.CheckSquare className="h-4.5 w-4.5 text-primary" />
          <h4 className="text-sm font-extrabold text-text-primary uppercase tracking-wider">
            Getting Started Checklist
          </h4>
        </div>

        {/* Task Checklist Items */}
        <div className="flex flex-col gap-2.5 mt-1">
          {tasks.map((task, idx) => (
            <div key={idx} className="flex items-start gap-2.5">
              <div
                className={cn(
                  'h-4.5 w-4.5 rounded-md border flex items-center justify-center shrink-0 mt-0.5 transition-colors duration-200',
                  task.completed
                    ? 'bg-success border-success text-white'
                    : 'border-text-muted/40 bg-transparent'
                )}
              >
                {task.completed && <LucideIcons.Check className="h-3 w-3 stroke-[3px]" />}
              </div>
              <span
                className={cn(
                  'text-xs font-bold leading-normal',
                  task.completed ? 'text-text-muted line-through' : 'text-text-secondary'
                )}
              >
                {task.text}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Checklist Completion Footer progress bar */}
      <div className="border-t border-border/50 pt-3 mt-4 flex items-center justify-between text-[10px] font-bold text-text-muted">
        <span>Setup Progress</span>
        <span>33% Complete</span>
      </div>
      <div className="w-full bg-muted h-1 rounded-full mt-1.5 overflow-hidden">
        <div className="bg-success h-full transition-all duration-500" style={{ width: '33%' }} />
      </div>
    </div>
  );
}

export default DashboardWelcome;
