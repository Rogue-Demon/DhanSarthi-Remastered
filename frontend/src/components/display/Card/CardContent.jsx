import React from 'react';
import { cn } from '@/utils';

export function CardContent({ children, className, ...props }) {
  return (
    <div className={cn('text-body-md text-text-primary', className)} {...props}>
      {children}
    </div>
  );
}

export default CardContent;
