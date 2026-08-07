import React from 'react';
import { cn } from '@/utils';

export function CardFooter({ children, className, ...props }) {
  return (
    <div className={cn('flex items-center gap-2 pt-2 border-t border-border mt-auto', className)} {...props}>
      {children}
    </div>
  );
}

export default CardFooter;
