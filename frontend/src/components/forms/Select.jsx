import React, { forwardRef } from 'react';
import { cn } from '@/utils';

export const Select = forwardRef(({
  children,
  className,
  error = false,
  success = false,
  disabled = false,
  ...props
}, ref) => {
  return (
    <div className="relative w-full flex items-center">
      <select
        ref={ref}
        disabled={disabled}
        className={cn(
          'w-full bg-card border border-border text-text-primary px-4 py-3 pr-10 rounded-input text-base transition-all duration-200 outline-none shadow-sm focus:ring-2 focus:ring-primary/40 focus:border-primary appearance-none cursor-pointer',
          error && 'border-destructive focus:ring-destructive/30 focus:border-destructive',
          success && 'border-success focus:ring-success/30 focus:border-success',
          disabled && 'opacity-60 bg-muted cursor-not-allowed pointer-events-none',
          className
        )}
        {...props}
      >
        {children}
      </select>
      <span className="absolute right-4 text-text-muted pointer-events-none flex items-center justify-center">
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </span>
    </div>
  );
});

Select.displayName = 'Select';
export default Select;
