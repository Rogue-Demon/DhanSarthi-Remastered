import React from 'react';
import { cn } from '@/utils';

export function CardDescription({ children, className, ...props }) {
  return (
    <p className={cn('text-body-sm text-text-secondary', className)} {...props}>
      {children}
    </p>
  );
}

export default CardDescription;
