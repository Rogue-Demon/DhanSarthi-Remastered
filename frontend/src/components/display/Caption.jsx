import React from 'react';
import { cn } from '@/utils';

export const Caption = ({
  children,
  className,
  as = 'span',
  ...props
}) => {
  const Tag = as;
  return (
    <Tag
      className={cn('text-caption-md text-text-muted select-none', className)}
      {...props}
    >
      {children}
    </Tag>
  );
};

export default Caption;
