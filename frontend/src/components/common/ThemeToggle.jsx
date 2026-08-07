import React from 'react';
import { useTheme } from '@/hooks';
import IconButton from '@/components/ui/IconButton';
import { THEMES } from '@/constants';

export function ThemeToggle({ className, ...props }) {
  const { theme, setTheme, isDark } = useTheme();

  const toggle = () => {
    setTheme(isDark ? THEMES.LIGHT : THEMES.DARK);
  };

  const sunIcon = (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707m12.728 0l-.707-.707M6.343 6.343l-.707-.707m12.728 5.657a9 9 0 11-12.728 0 9 9 0 0112.728 0z" />
    </svg>
  );

  const moonIcon = (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
      <path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
    </svg>
  );

  return (
    <IconButton
      icon={isDark ? sunIcon : moonIcon}
      onClick={toggle}
      tooltip={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      className={className}
      {...props}
    />
  );
}

export default ThemeToggle;
