import React from 'react';
import { cn } from '@/utils';

export const Surface = ({
  children,
  className,
  interactive = false,
  ...props
}) => {
  return (
    <div
      className={cn(
        interactive ? 'clay-surface-interactive' : 'clay-surface',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export default Surface;
