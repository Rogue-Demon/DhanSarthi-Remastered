import React from 'react';
import { cn } from '@/utils';

export const GradientText = ({
  children,
  className,
  as = 'span',
  variant = 'primary', // primary, hero
  ...props
}) => {
  const Tag = as;
  const gradientClass = variant === 'hero' ? 'gradient-text-hero' : 'gradient-text';

  return (
    <Tag
      className={cn(gradientClass, className)}
      {...props}
    >
      {children}
    </Tag>
  );
};

export default GradientText;
