import React from 'react';
import { cn } from '@/utils';

export const EmptyCard = ({
  children,
  className,
  title,
  description,
  action,
  ...props
}) => {
  return (
    <div
      className={cn(
        'border-2 border-dashed border-border rounded-xl p-8 flex flex-col items-center justify-center text-center gap-4 bg-transparent',
        className
      )}
      {...props}
    >
      <div className="flex flex-col gap-1">
        {title && <span className="font-bold text-text-primary text-base">{title}</span>}
        {description && <p className="text-sm text-text-secondary max-w-xs">{description}</p>}
      </div>
      {children}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
};

export default EmptyCard;
