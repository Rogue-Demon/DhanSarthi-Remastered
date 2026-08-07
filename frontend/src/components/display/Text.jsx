import React from 'react';
import { cn } from '@/utils';

export const Text = ({
  children,
  className,
  as = 'p',
  variant = 'md', // sm, md, lg, xl, muted
  ...props
}) => {
  const Tag = as;

  const variants = {
    sm: 'text-body-sm text-text-secondary',
    md: 'text-body-md text-text-primary',
    lg: 'text-body-lg text-text-primary',
    xl: 'text-body-xl text-text-primary',
    muted: 'text-body-md text-text-muted',
  };

  return (
    <Tag
      className={cn(variants[variant] || variants.md, className)}
      {...props}
    >
      {children}
    </Tag>
  );
};

export default Text;
