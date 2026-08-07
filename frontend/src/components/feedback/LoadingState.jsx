import React from 'react';
import { Skeleton } from './Skeleton';
import { cn } from '@/utils';

export const LoadingState = ({
  message = 'Loading dashboard...',
  className,
  ...props
}) => {
  return (
    <div className={cn('flex flex-col items-center justify-center p-8 gap-3 min-h-[200px]', className)} {...props}>
      <Skeleton width="3rem" height="3rem" className="mb-4" />
      <span className="text-sm font-semibold text-text-secondary select-none">
        {message}
      </span>
    </div>
  );
};

export default LoadingState;
