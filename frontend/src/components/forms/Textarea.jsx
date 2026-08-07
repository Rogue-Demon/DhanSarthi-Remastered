import React, { forwardRef } from 'react';
import { cn } from '@/utils';

export const Textarea = forwardRef(({
  className,
  error = false,
  success = false,
  disabled = false,
  readOnly = false,
  rows = 4,
  maxLength,
  value = '',
  ...props
}, ref) => {
  return (
    <div className="relative w-full">
      <textarea
        ref={ref}
        rows={rows}
        maxLength={maxLength}
        value={value}
        disabled={disabled}
        readOnly={readOnly}
        className={cn(
          'w-full bg-card border border-border text-text-primary px-4 py-3 rounded-input text-base transition-all duration-200 outline-none shadow-sm focus:ring-2 focus:ring-primary/40 focus:border-primary resize-y',
          error && 'border-destructive focus:ring-destructive/30 focus:border-destructive',
          success && 'border-success focus:ring-success/30 focus:border-success',
          disabled && 'opacity-60 bg-muted cursor-not-allowed pointer-events-none',
          readOnly && 'bg-muted cursor-default',
          className
        )}
        {...props}
      />
      {maxLength && (
        <span className="absolute bottom-3 right-4 text-xs text-text-muted select-none">
          {value.length}/{maxLength}
        </span>
      )}
    </div>
  );
});

Textarea.displayName = 'Textarea';
export default Textarea;
