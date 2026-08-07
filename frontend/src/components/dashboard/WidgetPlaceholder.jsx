import React from 'react';
import WidgetContainer from './WidgetContainer';
import WidgetActions from './WidgetActions';
import { Badge } from '@/components/ui';
import * as LucideIcons from 'lucide-react';
import { cn } from '@/utils';

/**
 * WidgetPlaceholder Component
 *
 * Renders a stylized placeholder card for widgets that are not yet implemented.
 * Follows the "Coming Soon" styling without charts or real financial values.
 */
export function WidgetPlaceholder({ widget, sizeClass, ...props }) {
  if (!widget) return null;

  // Handler mocks for Actions
  const handleInfo = () => alert(`Info for: ${widget.title}`);
  const handleRefresh = () => console.log(`Refreshing widget: ${widget.id}`);

  const toolbar = (
    <WidgetActions onInfo={handleInfo} onRefresh={handleRefresh} />
  );

  return (
    <WidgetContainer
      title={widget.title}
      icon={widget.icon}
      color={widget.color}
      toolbar={toolbar}
      sizeClass={sizeClass}
      {...props}
    >
      <div className="flex flex-col justify-between items-start gap-4 h-full pt-2">
        {/* Description */}
        <p className="text-xs text-text-secondary font-medium leading-relaxed">
          {widget.description}
        </p>

        {/* Mock Premium Vector Graphics / Wireframe Elements */}
        <div className="w-full h-16 rounded-xl bg-muted/40 border border-dashed border-border/80 flex items-center justify-between px-4 overflow-hidden relative group">
          <div className="absolute inset-0 opacity-[0.03] bg-[radial-gradient(#7C3AED_1px,transparent_1px)] [background-size:12px_12px]" />
          
          <div className="flex items-center gap-2 z-10">
            <div
              className="h-7 w-7 rounded-lg flex items-center justify-center text-white shadow-sm"
              style={{ background: widget.color || 'var(--gradient-primary)' }}
            >
              {React.createElement(LucideIcons[widget.icon] || LucideIcons.Layers, {
                className: 'h-4 w-4',
              })}
            </div>
            <div className="flex flex-col gap-1">
              <div className="h-2 w-16 rounded bg-text-muted/20" />
              <div className="h-1.5 w-10 rounded bg-text-muted/15" />
            </div>
          </div>

          {/* Micro trend graph placeholder */}
          <div className="flex items-end gap-1 h-8 text-text-muted/20 z-10">
            <div className="h-3 w-1 rounded-sm bg-current" />
            <div className="h-5 w-1 rounded-sm bg-current" />
            <div className="h-4 w-1 rounded-sm bg-current" />
            <div className="h-7 w-1 rounded-sm bg-current" style={{ color: widget.color }} />
          </div>
        </div>

        {/* Coming Soon status indicator row */}
        <div className="flex items-center justify-between w-full border-t border-border/50 pt-3 mt-2 shrink-0">
          <Badge
            variant="secondary"
            className="text-[10px] font-black tracking-widest uppercase bg-primary/10 border-primary/20 text-primary py-0.5 px-2 rounded-full"
          >
            Coming Soon
          </Badge>
          <div className="flex items-center gap-1 text-[10px] font-bold text-text-muted">
            <LucideIcons.Sparkles className="h-3 w-3 animate-pulse text-accent" />
            <span>AI Powered module</span>
          </div>
        </div>
      </div>
    </WidgetContainer>
  );
}

export default WidgetPlaceholder;
