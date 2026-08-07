import React from 'react';
import { cn } from '@/utils';

export const Divider = ({
  className,
  orientation = 'horizontal',
  inset = false,
  ...props
}) => {
  return (
    <div
      role="none"
      className={cn(
        'bg-border flex-shrink-0',
        orientation === 'horizontal' ? 'h-[1px] w-full' : 'h-full w-[1px]',
        inset && orientation === 'horizontal' && 'mx-4',
        inset && orientation === 'vertical' && 'my-4',
        className
      )}
      {...props}
    />
  );
};

export default Divider;
