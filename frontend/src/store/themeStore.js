import { create } from 'zustand';
import { STORAGE_KEYS, THEMES } from '@/constants';

export const useThemeStore = create((set) => ({
  theme: localStorage.getItem(STORAGE_KEYS.THEME) || THEMES.SYSTEM,
  setTheme: (theme) => {
    localStorage.setItem(STORAGE_KEYS.THEME, theme);
    set({ theme });
  },
}));

export default useThemeStore;
