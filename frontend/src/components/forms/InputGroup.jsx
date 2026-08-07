import React from 'react';
import { cn } from '@/utils';

export function InputGroup({ children, className, ...props }) {
  return (
    <div className={cn('flex flex-col gap-1.5 w-full', className)} {...props}>
      {children}
    </div>
  );
}

export default InputGroup;
