import React from 'react';
import { cn } from '@/utils';

export function Spinner({ size = 'md', className, ...props }) {
  const sizes = {
    sm: 'h-4 w-4 border-2',
    md: 'h-8 w-8 border-3',
    lg: 'h-12 w-12 border-4',
  };

  return (
    <div
      role="status"
      className={cn(
        'animate-spin rounded-full border-t-primary border-r-transparent border-b-transparent border-l-transparent',
        sizes[size] || sizes.md,
        className
      )}
      {...props}
    >
      <span className="sr-only">Loading...</span>
    </div>
  );
}

export default Spinner;
