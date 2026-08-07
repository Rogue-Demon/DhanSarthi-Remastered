import React from 'react';
import Card from './Card/Card';
import NumericValue from './NumericValue';
import { cn } from '@/utils';

export const StatCard = ({
  title,
  value,
  description,
  trend, // { value: number, isPositive: boolean }
  icon,
  className,
  type = 'currency',
  ...props
}) => {
  return (
    <Card className={cn('p-6', className)} {...props}>
      <div className="flex items-start justify-between">
        <div className="flex flex-col gap-1">
          <span className="text-sm font-semibold text-text-secondary">{title}</span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold tracking-tight text-text-primary">
              {typeof value === 'number' ? (
                <NumericValue value={value} type={type} />
              ) : (
                value
              )}
            </span>
          </div>
        </div>
        {icon && (
          <div className="rounded-xl bg-primary/10 p-3 text-primary flex items-center justify-center">
            {icon}
          </div>
        )}
      </div>

      <div className="flex items-center gap-2 mt-2">
        {trend && (
          <span
            className={cn(
              'inline-flex items-center gap-0.5 text-xs font-bold px-2 py-0.5 rounded-full',
              trend.isPositive
                ? 'bg-success/15 text-success'
                : 'bg-destructive/15 text-destructive'
            )}
          >
            {trend.isPositive ? '+' : '-'}
            {Math.abs(trend.value)}%
          </span>
        )}
        {description && (
          <span className="text-xs text-text-muted">{description}</span>
        )}
      </div>
    </Card>
  );
};

export default StatCard;
