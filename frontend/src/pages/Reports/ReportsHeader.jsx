import React from 'react';
import { useProfile } from '@/hooks';
import { Badge, Button } from '@/components/ui';
import * as LucideIcons from 'lucide-react';
import { cn } from '@/utils';

/**
 * ReportsHeader Component
 * Header bar for Reports & Analytics module with date picker, filters, and export toolbar.
 */
export function ReportsHeader({ className, ...props }) {
  const { profile, profileConfig } = useProfile();

  const getHeaderTitle = () => {
    switch (profile) {
      case 'Student':
        return 'Student Financial Statements';
      case 'Working Professional':
        return 'Executive Wealth Analytics';
      case 'Business':
        return 'Enterprise Financial Reports';
      default:
        return 'Financial Reports & Analytics';
    }
  };

  return (
    <div
      className={cn(
        'flex flex-col xl:flex-row xl:items-center justify-between gap-4 w-full select-none pb-4 border-b border-border/40',
        className
      )}
      {...props}
    >
      {/* Title block */}
      <div className="flex flex-col text-left gap-1">
        <div className="flex flex-wrap items-center gap-2.5">
          <h2 className="text-2xl font-black text-text-primary tracking-tight">
            {getHeaderTitle()}
          </h2>
          {profileConfig && (
            <Badge
              variant="secondary"
              className="text-[9px] font-black uppercase tracking-widest px-2.5 py-0.5 rounded-md border"
              style={{
                color: profileConfig.color,
                borderColor: `${profileConfig.color}25`,
                background: `${profileConfig.color}10`,
              }}
            >
              {profileConfig.label} Mode
            </Badge>
          )}
        </div>
        <p className="text-xs font-bold text-text-muted">
          Enterprise interactive data visualizations, cash flows, and performance metrics.
        </p>
      </div>

      {/* Reusable UI Filters & Quick Actions toolbar */}
      <div className="flex flex-wrap items-center gap-3.5">
        {/* Search input */}
        <div className="relative w-44">
          <LucideIcons.Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-text-muted" />
          <input
            type="text"
            placeholder="Search metrics..."
            disabled
            className="w-full pl-9 pr-3 py-1.5 text-xs font-bold rounded-xl border border-border bg-card/60 text-text-muted cursor-not-allowed focus:outline-none"
          />
        </div>

        {/* Date Range Selector */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-border bg-card/60 text-xs font-bold text-text-secondary cursor-not-allowed">
          <LucideIcons.Calendar className="h-3.5 w-3.5 text-text-muted" />
          <span>Year 2026</span>
          <LucideIcons.ChevronDown className="h-3.5 w-3.5 text-text-muted ml-1" />
        </div>

        {/* Filter selection */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-border bg-card/60 text-xs font-bold text-text-secondary cursor-not-allowed">
          <LucideIcons.Filter className="h-3.5 w-3.5 text-text-muted" />
          <span>Filter (All)</span>
          <LucideIcons.ChevronDown className="h-3.5 w-3.5 text-text-muted ml-1" />
        </div>

        {/* Export button */}
        <Button
          variant="secondary"
          size="sm"
          className="rounded-xl font-bold text-xs gap-1.5 px-3 py-2 border-border shadow-xs text-text-secondary bg-card"
          onClick={() => console.log('Export analytics clicked')}
          iconLeft={<LucideIcons.Download className="h-3.5 w-3.5" />}
        >
          Export Report
        </Button>
      </div>
    </div>
  );
}

export default ReportsHeader;
