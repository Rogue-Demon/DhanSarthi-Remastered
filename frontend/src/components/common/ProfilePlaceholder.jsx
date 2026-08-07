import React from 'react';
import { useProfile } from '@/hooks';
import Avatar from '@/components/ui/Avatar';
import { cn } from '@/utils';

export function ProfilePlaceholder({ className, ...props }) {
  const { profile } = useProfile();

  return (
    <div className={cn('flex items-center gap-3 bg-muted/40 p-2.5 rounded-xl border border-border', className)} {...props}>
      <Avatar name="Shreyanshu" size="sm" online />
      <div className="flex flex-col select-none">
        <span className="text-sm font-bold text-text-primary">Shreyanshu</span>
        <span className="text-[10px] font-bold text-primary uppercase tracking-wider">{profile}</span>
      </div>
    </div>
  );
}

export default ProfilePlaceholder;
