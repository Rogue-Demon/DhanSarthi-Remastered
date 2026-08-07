import React from 'react';
import { cn } from '@/utils';

export function Logo({ className, size = 'md', ...props }) {
  const sizes = {
    sm: 'h-6 w-6',
    md: 'h-8 w-8',
    lg: 'h-10 w-10',
  };

  return (
    <div className={cn('flex items-center justify-center text-primary', className)} {...props}>
      <svg
        className={cn(sizes[size] || sizes.md)}
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <rect width="32" height="32" rx="8" fill="url(#logo-grad)" />
        <path
          d="M16 8L24 16H8L16 8Z"
          fill="white"
        />
        <path
          d="M16 24L8 16H24L16 24Z"
          fill="white"
          fillOpacity="0.7"
        />
        <circle cx="16" cy="16" r="3" fill="#7C3AED" />
        <defs>
          <linearGradient id="logo-grad" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
            <stop stopColor="#7C3AED" />
            <stop offset="1" stopColor="#C084FC" />
          </linearGradient>
        </defs>
      </svg>
    </div>
  );
}

export default Logo;
