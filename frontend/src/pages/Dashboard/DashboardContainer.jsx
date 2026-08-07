import React from 'react';
import { cn } from '@/utils';

/**
 * DashboardContainer Component
 *
 * Page-level structural container wrapper for the dashboard view.
 * Ensures consistent padding and spacing across desktop, laptop, tablet, and mobile.
 */
export function DashboardContainer({ children, className, ...props }) {
  return (
    <div
      className={cn(
        'w-full max-w-[1400px] mx-auto flex flex-col gap-8 pb-12 animate-fade-in text-left',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export default DashboardContainer;
