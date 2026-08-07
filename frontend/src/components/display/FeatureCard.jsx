import React from 'react';
import Card from './Card/Card';
import { cn } from '@/utils';

export const FeatureCard = ({
  title,
  description,
  icon,
  className,
  children,
  onClick,
  ...props
}) => {
  return (
    <Card
      interactive={!!onClick}
      onClick={onClick}
      className={cn('p-6 flex flex-col gap-3', className)}
      {...props}
    >
      {icon && (
        <div className="rounded-2xl bg-primary/10 text-primary p-4 w-fit flex items-center justify-center">
          {icon}
        </div>
      )}
      <div className="flex flex-col gap-1.5">
        <h4 className="text-lg font-bold text-text-primary">{title}</h4>
        <p className="text-sm text-text-secondary leading-relaxed">{description}</p>
      </div>
      {children}
    </Card>
  );
};

export default FeatureCard;
