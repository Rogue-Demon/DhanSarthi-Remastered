import React from 'react';
import { cn } from '@/utils';

export function HelperText({ children, className, ...props }) {
  return (
    <p className={cn('text-xs text-text-muted mt-1 leading-normal select-none', className)} {...props}>
      {children}
    </p>
  );
}

export default HelperText;
