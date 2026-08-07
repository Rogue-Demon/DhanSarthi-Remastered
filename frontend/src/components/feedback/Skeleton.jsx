import React from 'react';
import { cn } from '@/utils';

export function Skeleton({ className, variant = 'rectangular', ...props }) {
  return (
    <div
      className={cn(
        'animate-pulse bg-muted',
        variant === 'circular' ? 'rounded-full' : 'rounded-md',
        className
      )}
      {...props}
    />
  );
}

export default Skeleton;
