import React from 'react';
import { useProfile } from '@/hooks';
import Dropdown, { MenuItem } from '@/components/overlay/Dropdown';
import Avatar from '@/components/ui/Avatar';
import { cn } from '@/utils';

export function ProfileMenu({ className, ...props }) {
  const { profile } = useProfile();

  const menuItems = [
    <div key="header" className="px-3 py-2 flex flex-col border-b border-border select-none">
      <span className="text-sm font-bold text-text-primary">Shreyanshu</span>
      <span className="text-xs text-text-muted">{profile}</span>
    </div>,
    <MenuItem key="profile" className="mt-1">
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
      </svg>
      My Profile
    </MenuItem>,
    <MenuItem key="settings">
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
      Settings
    </MenuItem>,
    <MenuItem key="logout" destructive className="border-t border-border mt-1">
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
      </svg>
      Logout
    </MenuItem>,
  ];

  return (
    <Dropdown menuItems={menuItems} align="right" className={cn('flex items-center', className)} {...props}>
      <div className="flex items-center gap-2 cursor-pointer select-none">
        <Avatar name="Shreyanshu" size="sm" />
      </div>
    </Dropdown>
  );
}

export default ProfileMenu;
