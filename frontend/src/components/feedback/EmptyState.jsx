import React from 'react';
import { cn } from '@/utils';
import Button from '@/components/ui/Button';

export const EmptyState = ({
  title = 'No data available',
  description = 'There is nothing to display here right now.',
  illustration,
  actionText,
  onAction,
  secondaryActionText,
  onSecondaryAction,
  className,
  ...props
}) => {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center p-8 text-center max-w-sm mx-auto gap-4',
        className
      )}
      {...props}
    >
      {illustration ? (
        <div className="mb-2 text-text-muted">{illustration}</div>
      ) : (
        <div className="mb-2 rounded-2xl bg-muted p-4 text-text-muted flex items-center justify-center">
          <svg className="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0a2 2 0 01-2 2H6a2 2 0 01-2-2m16 0V9a2 2 0 00-2-2H6a2 2 0 00-2 2v4m16 0H4" />
          </svg>
        </div>
      )}
      <div className="flex flex-col gap-1">
        <h4 className="text-lg font-bold text-text-primary">{title}</h4>
        <p className="text-sm text-text-secondary">{description}</p>
      </div>
      {(actionText || secondaryActionText) && (
        <div className="flex items-center gap-3 mt-2">
          {secondaryActionText && onSecondaryAction && (
            <Button variant="secondary" onClick={onSecondaryAction}>
              {secondaryActionText}
            </Button>
          )}
          {actionText && onAction && (
            <Button variant="primary" onClick={onAction}>
              {actionText}
            </Button>
          )}
        </div>
      )}
    </div>
  );
};

export default EmptyState;
