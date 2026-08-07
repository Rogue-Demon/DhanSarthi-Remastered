import React from 'react';
import * as LucideIcons from 'lucide-react';
import { cn } from '@/utils';

/**
 * WidgetTitle Component
 * Renders the widget icon and header text.
 */
export function WidgetTitle({ title, icon, color, className, ...props }) {
  const IconComponent = icon && LucideIcons[icon];

  return (
    <div className={cn('flex items-center gap-3 select-none', className)} {...props}>
      {IconComponent && (
        <div
          className="p-2 rounded-xl flex items-center justify-center shrink-0 border border-white/20 dark:border-white/5 shadow-xs"
          style={{
            background: color ? `${color}15` : 'var(--muted)',
            color: color || 'var(--text-secondary)',
          }}
        >
          <IconComponent className="h-4.5 w-4.5 stroke-[2px]" />
        </div>
      )}
      <h4 className="text-base font-extrabold text-text-primary tracking-tight leading-none">
        {title}
      </h4>
    </div>
  );
}

export default WidgetTitle;
