import React from 'react';
import { cn } from '@/utils';

/**
 * WidgetToolbar Component
 * Layout wrapper for widget actions.
 */
export function WidgetToolbar({ children, className, ...props }) {
  return (
    <div className={cn('flex items-center gap-2 select-none', className)} {...props}>
      {children}
    </div>
  );
}

export default WidgetToolbar;
