import React from 'react';
import { cn } from '@/utils';

export const Label = ({
  children,
  className,
  htmlFor,
  ...props
}) => {
  return (
    <label
      htmlFor={htmlFor}
      className={cn(
        'text-label-md font-semibold text-text-secondary select-none cursor-pointer',
        className
      )}
      {...props}
    >
      {children}
    </label>
  );
};

export default Label;
