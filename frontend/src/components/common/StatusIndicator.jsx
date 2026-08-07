import React from 'react';
import { cn } from '@/utils';

export function StatusIndicator({ status = 'online', label, className, ...props }) {
  const styles = {
    online: 'bg-success',
    offline: 'bg-text-muted',
    away: 'bg-warning',
    busy: 'bg-destructive',
  };

  return (
    <div className={cn('inline-flex items-center gap-2 select-none', className)} {...props}>
      <span className={cn('h-2 w-2 rounded-full', styles[status] || styles.online)} />
      {label && <span className="text-xs font-semibold text-text-secondary">{label}</span>}
    </div>
  );
}

export default StatusIndicator;
