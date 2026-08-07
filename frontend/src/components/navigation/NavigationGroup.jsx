import React from 'react';
import { cn } from '@/utils';

export function NavigationGroup({ children, className, label, collapsed = false, ...props }) {
  return (
    <div className={cn('flex flex-col gap-1 w-full', className)} {...props}>
      {label && !collapsed && (
        <span className="px-4 py-1.5 text-xs font-bold text-text-muted uppercase tracking-wider select-none">
          {label}
        </span>
      )}
      {children}
    </div>
  );
}

export default NavigationGroup;
