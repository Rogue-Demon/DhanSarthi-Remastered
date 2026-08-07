import React from 'react';
import { cn } from '@/utils';

export function FieldLabel({ children, className, htmlFor, required, ...props }) {
  return (
    <label
      htmlFor={htmlFor}
      className={cn('text-sm font-semibold text-text-secondary select-none flex items-center gap-1.5', className)}
      {...props}
    >
      {children}
      {required && <span className="text-destructive font-bold">*</span>}
    </label>
  );
}

export default FieldLabel;
