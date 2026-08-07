import React from 'react';
import { useTheme } from '@/hooks';
import { ThemeContext } from '@/contexts';

export function ThemeProvider({ children }) {
  const { theme, setTheme, isDark } = useTheme();

  return (
    <ThemeContext.Provider value={{ theme, setTheme, isDark }}>
      {children}
    </ThemeContext.Provider>
  );
}

export default ThemeProvider;
