import React from 'react';
import { useProfile } from '@/hooks';
import { Badge } from '@/components/ui';
import { cn } from '@/utils';

export function SettingsHeader({ className, ...props }) {
  const { profileConfig } = useProfile();

  return (
    <div
      className={cn(
        'flex flex-col sm:flex-row sm:items-center justify-between gap-4 w-full select-none pb-4 border-b border-border/40 text-left',
        className
      )}
      {...props}
    >
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2.5">
          <h2 className="text-2xl font-black text-text-primary tracking-tight">
            Account Preferences & Settings
          </h2>
          {profileConfig && (
            <Badge
              variant="secondary"
              className="text-[9px] font-black uppercase tracking-widest px-2.5 py-0.5 rounded-md border"
              style={{
                color: profileConfig.color,
                borderColor: `${profileConfig.color}25`,
                background: `${profileConfig.color}10`,
              }}
            >
              {profileConfig.label} Mode
            </Badge>
          )}
        </div>
        <p className="text-xs font-bold text-text-muted">
          Manage profile parameters, themes, notifications, security, and accessibility.
        </p>
      </div>
    </div>
  );
}

export default SettingsHeader;
