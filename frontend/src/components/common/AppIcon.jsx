import React from 'react';
import { cn } from '@/utils';

export function AppIcon({ className, size = 'md', ...props }) {
  const sizes = {
    sm: 'h-6 w-6',
    md: 'h-8 w-8',
    lg: 'h-10 w-10',
  };

  return (
    <div className={cn('rounded-lg bg-primary/10 text-primary p-1.5 flex items-center justify-center', sizes[size] || sizes.md, className)} {...props}>
      <svg className="h-full w-full stroke-current" fill="none" viewBox="0 0 24 24" strokeWidth="2.5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M12 16v1" />
      </svg>
    </div>
  );
}

export default AppIcon;
