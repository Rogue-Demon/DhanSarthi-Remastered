import React from 'react';
import { cn } from '@/utils';

export function NotificationBadge({ count = 0, className, ...props }) {
  if (count <= 0) return null;

  return (
    <span
      className={cn(
        'absolute -top-1.5 -right-1.5 bg-destructive text-white text-[10px] font-extrabold h-5 w-5 rounded-full flex items-center justify-center border-2 border-card shadow-sm animate-scaleIn select-none',
        className
      )}
      {...props}
    >
      {count > 9 ? '9+' : count}
    </span>
  );
}

export default NotificationBadge;
