import React from 'react';
import { cn } from '@/utils';

export function CardHeader({ children, className, ...props }) {
  return (
    <div className={cn('flex flex-col gap-1.5', className)} {...props}>
      {children}
    </div>
  );
}

export default CardHeader;
