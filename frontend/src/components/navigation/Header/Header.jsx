import React from 'react';
import { useSidebar } from '@/hooks';
import Breadcrumb from '../Breadcrumb/Breadcrumb';
import SearchBar from '../SearchBar/SearchBar';
import NotificationButton from '../NotificationButton/NotificationButton';
import ThemeSwitcher from '../ThemeSwitcher/ThemeSwitcher';
import ProfileMenu from '../ProfileMenu/ProfileMenu';
import IconButton from '@/components/ui/IconButton';
import { cn } from '@/utils';

export function Header({ className, ...props }) {
  const { toggleMobileOpen } = useSidebar();

  const menuIcon = (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  );

  return (
    <header
      className={cn(
        'sticky top-0 right-0 z-20 flex items-center justify-between h-16 px-4 md:px-6 bg-card/85 backdrop-blur-md border-b border-border select-none clay-surface-flat',
        className
      )}
      {...props}
    >
      <div className="flex items-center gap-4">
        <IconButton
          icon={menuIcon}
          onClick={toggleMobileOpen}
          tooltip="Open Navigation Menu"
          className="md:hidden"
        />
        <Breadcrumb />
      </div>

      <div className="flex items-center gap-3">
        <SearchBar className="hidden md:flex" />
        <NotificationButton />
        <ThemeSwitcher />
        <div className="h-8 w-[1px] bg-border mx-1" />
        <ProfileMenu />
      </div>
    </header>
  );
}

export default Header;
