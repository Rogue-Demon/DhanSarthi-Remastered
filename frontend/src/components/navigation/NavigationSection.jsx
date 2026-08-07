import React from 'react';
import { cn } from '@/utils';

export function NavigationSection({ children, className, ...props }) {
  return (
    <div className={cn('flex flex-col gap-6 py-2 w-full', className)} {...props}>
      {children}
    </div>
  );
}

export default NavigationSection;
