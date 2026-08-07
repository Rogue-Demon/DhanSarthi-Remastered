import React from 'react';
import { cn } from '@/utils';

export function CardTitle({ children, className, as = 'h3', ...props }) {
  const Tag = as;
  return (
    <Tag className={cn('text-title-lg font-bold text-text-primary tracking-tight', className)} {...props}>
      {children}
    </Tag>
  );
}

export default CardTitle;
