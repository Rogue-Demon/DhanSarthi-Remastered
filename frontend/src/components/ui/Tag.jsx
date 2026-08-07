import React from 'react';
import { cn } from '@/utils';

export const Tag = ({
  children,
  className,
  variant = 'primary',
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-medium rounded-md px-2 py-0.5 text-xs select-none border';

  const variants = {
    primary: 'bg-primary/5 text-primary border-primary/10',
    secondary: 'bg-muted text-text-secondary border-border',
    success: 'bg-success/5 text-success border-success/10',
    warning: 'bg-warning/5 text-warning border-warning/10',
    danger: 'bg-destructive/5 text-destructive border-destructive/10',
  };

  return (
    <span
      className={cn(baseStyles, variants[variant], className)}
      {...props}
    >
      {children}
    </span>
  );
};

export default Tag;
