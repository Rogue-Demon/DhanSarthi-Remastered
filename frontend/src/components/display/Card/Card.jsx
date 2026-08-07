import React, { forwardRef } from 'react';
import { cn } from '@/utils';

export const Card = forwardRef(({
  children,
  className,
  interactive = false,
  ...props
}, ref) => {
  const cardClasses = cn(
    interactive ? 'clay-surface-interactive cursor-pointer' : 'clay-surface',
    'bg-card p-6 flex flex-col gap-4',
    className
  );

  return (
    <div
      ref={ref}
      className={cardClasses}
      {...props}
    >
      {children}
    </div>
  );
});

Card.displayName = 'Card';
export default Card;
