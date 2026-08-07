import React from 'react';
import { cn } from '@/utils';

export const Heading = ({
  children,
  className,
  level = 2, // 1 to 6
  variant, // Option to override default size mappings
  ...props
}) => {
  const Tag = `h${level}`;

  const defaultSizes = {
    1: 'text-display-xl font-bold tracking-tight',
    2: 'text-display-md font-bold tracking-tight',
    3: 'text-title-lg font-semibold',
    4: 'text-title-md font-semibold',
    5: 'text-title-sm font-medium',
    6: 'text-body-lg font-medium',
  };

  const sizes = {
    'display-xl': 'text-display-xl font-bold tracking-tight',
    'display-lg': 'text-display-lg font-bold tracking-tight',
    'display-md': 'text-display-md font-bold tracking-tight',
    'title-lg': 'text-title-lg font-semibold',
    'title-md': 'text-title-md font-semibold',
    'title-sm': 'text-title-sm font-medium',
  };

  return (
    <Tag
      className={cn(
        'text-text-primary',
        variant ? sizes[variant] : defaultSizes[level],
        className
      )}
      {...props}
    >
      {children}
    </Tag>
  );
};

export default Heading;
