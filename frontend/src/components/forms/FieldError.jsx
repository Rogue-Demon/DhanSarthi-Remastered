import React from 'react';
import { cn } from '@/utils';

export function FieldError({ children, className, ...props }) {
  if (!children) return null;
  
  return (
    <p className={cn('text-xs text-destructive mt-1 font-semibold flex items-center gap-1 select-none animate-fadeIn', className)} {...props}>
      <svg className="h-3 w-3 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      {children}
    </p>
  );
}

export default FieldError;
