import React from 'react';
import { cn } from '@/utils';

export const Container = ({
  children,
  className,
  fluid = false,
  ...props
}) => {
  return (
    <div
      className={cn(
        fluid ? 'w-full px-4 md:px-6 lg:px-8' : 'page-container',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export default Container;
