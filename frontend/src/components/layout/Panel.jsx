import React from 'react';
import { cn } from '@/utils';

export const Panel = ({
  children,
  className,
  ...props
}) => {
  return (
    <div
      className={cn(
        'bg-card rounded-2xl border border-border shadow-md p-6',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export default Panel;
