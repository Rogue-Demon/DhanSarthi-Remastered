import React from 'react';
import Card from './Card/Card';
import { cn } from '@/utils';

export const InfoCard = ({
  title,
  description,
  variant = 'info', // info, success, warning, danger
  icon,
  className,
  children,
  ...props
}) => {
  const styles = {
    info: 'bg-primary/5 border-primary/10 text-primary',
    success: 'bg-success/5 border-success/10 text-success',
    warning: 'bg-warning/5 border-warning/10 text-warning',
    danger: 'bg-destructive/5 border-destructive/10 text-destructive',
  };

  return (
    <Card className={cn('p-5 border flex flex-row items-start gap-4', styles[variant] || styles.info, className)} {...props}>
      {icon && (
        <div className="flex-shrink-0 mt-0.5">
          {icon}
        </div>
      )}
      <div className="flex flex-col gap-1 flex-1">
        {title && <span className="font-bold text-text-primary text-base">{title}</span>}
        {description && <p className="text-sm text-text-secondary">{description}</p>}
        {children}
      </div>
    </Card>
  );
};

export default InfoCard;
