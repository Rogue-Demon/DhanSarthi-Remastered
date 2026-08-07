import React from 'react';
import { cn } from '@/utils';

/**
 * DashboardGrid Component
 *
 * A reusable responsive 12-column layout wrapper.
 * Adapts grid columns:
 * - Desktop/Laptop: 12-columns grid with specific widget item column spans (col-span-x)
 * - Tablet: 2-columns grid layout
 * - Mobile: 1-column layout
 */
export function DashboardGrid({ children, className, ...props }) {
  return (
    <div
      className={cn(
        'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-6 w-full auto-rows-max',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export default DashboardGrid;
