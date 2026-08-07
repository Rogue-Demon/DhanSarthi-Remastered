import React from 'react';
import { useProfile } from '@/hooks';
import { PROFILES } from '@/constants';
import Dropdown, { MenuItem } from '@/components/overlay/Dropdown';
import Avatar from '@/components/ui/Avatar';
import { cn } from '@/utils';

export function UserSwitcher({ collapsed = false, className, ...props }) {
  const { profile, setProfile } = useProfile();

  const handleProfileChange = (selected) => {
    setProfile(selected);
  };

  const dropdownItems = Object.values(PROFILES).map((p) => (
    <MenuItem key={p} onClick={() => handleProfileChange(p)} className={cn(p === profile && 'text-primary bg-primary/5 font-bold')}>
      <div className="flex flex-col">
        <span className="text-sm">{p}</span>
      </div>
    </MenuItem>
  ));

  return (
    <div className={cn('flex items-center gap-3 w-full border border-border bg-muted/40 p-2.5 rounded-xl', className)} {...props}>
      <Dropdown menuItems={dropdownItems} align={collapsed ? 'left' : 'right'} className="w-full">
        <div className="flex items-center gap-3 w-full justify-between select-none cursor-pointer">
          <div className="flex items-center gap-3">
            <Avatar name="Shreyanshu" size="sm" online />
            {!collapsed && (
              <div className="flex flex-col text-left">
                <span className="text-sm font-bold text-text-primary">Shreyanshu</span>
                <span className="text-[10px] font-bold text-primary uppercase tracking-wider">{profile}</span>
              </div>
            )}
          </div>
          {!collapsed && (
            <svg className="h-4 w-4 text-text-muted flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 9l4 4 4-4" />
            </svg>
          )}
        </div>
      </Dropdown>
    </div>
  );
}

export default UserSwitcher;
