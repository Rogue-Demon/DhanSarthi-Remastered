import React from 'react';
import { useProfile } from '@/hooks';
import { Badge, Button } from '@/components/ui';
import * as LucideIcons from 'lucide-react';
import { cn } from '@/utils';

/**
 * DashboardHeader Component
 *
 * Dashboard-specific header. Renders the greeting message, date, current profile,
 * and quick actions placeholder (e.g. widget customize button, search bar).
 */
export function DashboardHeader({ className, ...props }) {
  const { profile, profileConfig } = useProfile();

  // Format today's date beautifully
  const getFormattedDate = () => {
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    return new Date().toLocaleDateString('en-US', options);
  };

  return (
    <div
      className={cn(
        'flex flex-col sm:flex-row sm:items-center justify-between gap-4 w-full select-none pb-2 border-b border-border/40',
        className
      )}
      {...props}
    >
      {/* User Greeting & Date */}
      <div className="flex flex-col text-left gap-1">
        <div className="flex flex-wrap items-center gap-2.5">
          <h1 className="text-3xl font-black text-text-primary tracking-tight">
            Welcome back, Shreyanshu!
          </h1>
          {profileConfig && (
            <Badge
              variant="secondary"
              className="text-[10px] font-black uppercase tracking-widest px-2.5 py-0.5 rounded-full border border-border shadow-xs"
              style={{
                color: profileConfig.color,
                borderColor: `${profileConfig.color}25`,
                background: `${profileConfig.color}10`,
              }}
            >
              {profileConfig.label}
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-1.5 text-xs font-bold text-text-muted mt-0.5">
          <LucideIcons.Calendar className="h-3.5 w-3.5" />
          <span>{getFormattedDate()}</span>
        </div>
      </div>

      {/* Search & Quick Actions Placeholder */}
      <div className="flex items-center gap-3 self-start sm:self-center">
        {/* Mock Search input */}
        <div className="relative hidden md:block w-48">
          <LucideIcons.Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
          <input
            type="text"
            placeholder="Search widgets..."
            disabled
            className="w-full pl-9 pr-3 py-1.5 text-xs font-bold rounded-xl border border-border bg-card/50 text-text-muted cursor-not-allowed focus:outline-none"
          />
        </div>

        {/* Quick action: Customize grid */}
        <Button
          variant="secondary"
          size="sm"
          className="rounded-xl font-bold text-xs gap-1.5 px-3 py-2 border-border shadow-sm text-text-secondary"
          onClick={() => console.log('Customize layout action clicked')}
          iconLeft={<LucideIcons.LayoutGrid className="h-3.5 w-3.5" />}
        >
          Customize Grid
        </Button>

        {/* Quick action: Export data */}
        <Button
          variant="ghost"
          size="sm"
          className="rounded-xl font-bold text-xs gap-1.5 px-3 py-2 hover:bg-muted text-text-muted"
          onClick={() => console.log('Export data clicked')}
          iconLeft={<LucideIcons.Download className="h-3.5 w-3.5" />}
        >
          Export
        </Button>
      </div>
    </div>
  );
}

export default DashboardHeader;
