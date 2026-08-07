import React from 'react';
import { cn } from '@/utils';

export const Timeline = ({
  items = [], // Array of { title, description, date, active }
  className,
  ...props
}) => {
  return (
    <div className={cn('flex flex-col gap-6 relative pl-6 border-l border-border', className)} {...props}>
      {items.map((item, index) => (
        <div key={index} className="relative flex flex-col gap-1">
          {/* Dot */}
          <span
            className={cn(
              'absolute -left-[31px] top-1.5 h-4.5 w-4.5 rounded-full border-4 border-background',
              item.active ? 'bg-primary' : 'bg-border'
            )}
          />
          {item.date && (
            <span className="text-xs text-text-muted font-medium">{item.date}</span>
          )}
          <span className="font-semibold text-text-primary text-base">{item.title}</span>
          {item.description && (
            <p className="text-sm text-text-secondary leading-relaxed">{item.description}</p>
          )}
        </div>
      ))}
    </div>
  );
};

export default Timeline;
