import React from 'react';
import { useTheme } from '@/hooks';
import Dropdown, { MenuItem } from '@/components/overlay/Dropdown';
import IconButton from '@/components/ui/IconButton';
import { THEMES } from '@/constants';
import { cn } from '@/utils';

export function ThemeSwitcher({ className, ...props }) {
  const { theme, setTheme } = useTheme();

  const themeIcon = (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707m12.728 0l-.707-.707M6.343 6.343l-.707-.707m12.728 5.657a9 9 0 11-12.728 0 9 9 0 0112.728 0z" />
    </svg>
  );

  const menuItems = [
    <MenuItem key={THEMES.LIGHT} onClick={() => setTheme(THEMES.LIGHT)} className={cn(theme === THEMES.LIGHT && 'text-primary bg-primary/5 font-bold')}>
      Light Mode
    </MenuItem>,
    <MenuItem key={THEMES.DARK} onClick={() => setTheme(THEMES.DARK)} className={cn(theme === THEMES.DARK && 'text-primary bg-primary/5 font-bold')}>
      Dark Mode
    </MenuItem>,
    <MenuItem key={THEMES.SYSTEM} onClick={() => setTheme(THEMES.SYSTEM)} className={cn(theme === THEMES.SYSTEM && 'text-primary bg-primary/5 font-bold')}>
      System Settings
    </MenuItem>,
  ];

  return (
    <Dropdown menuItems={menuItems} align="right" className={className} {...props}>
      <IconButton icon={themeIcon} size="md" tooltip="Theme Settings" />
    </Dropdown>
  );
}

export default ThemeSwitcher;
