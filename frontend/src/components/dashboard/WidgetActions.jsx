import React from 'react';
import { cn } from '@/utils';
import * as LucideIcons from 'lucide-react';
import IconButton from '@/components/ui/IconButton';

/**
 * WidgetActions Component
 * Standard set of actions (Refresh, Settings, Info, Expand) for widgets.
 */
export function WidgetActions({
  onRefresh,
  onSettings,
  onInfo,
  onExpand,
  className,
  ...props
}) {
  return (
    <div className={cn('flex items-center gap-1 text-text-muted', className)} {...props}>
      {onInfo && (
        <IconButton
          icon={<LucideIcons.Info className="h-4 w-4" />}
          onClick={onInfo}
          size="sm"
          variant="ghost"
          tooltip="Info"
        />
      )}
      {onRefresh && (
        <IconButton
          icon={<LucideIcons.RefreshCw className="h-4 w-4" />}
          onClick={onRefresh}
          size="sm"
          variant="ghost"
          tooltip="Refresh"
        />
      )}
      {onSettings && (
        <IconButton
          icon={<LucideIcons.Settings className="h-4 w-4" />}
          onClick={onSettings}
          size="sm"
          variant="ghost"
          tooltip="Configure"
        />
      )}
      {onExpand && (
        <IconButton
          icon={<LucideIcons.Maximize2 className="h-4 w-4" />}
          onClick={onExpand}
          size="sm"
          variant="ghost"
          tooltip="Expand"
        />
      )}
    </div>
  );
}

export default WidgetActions;
