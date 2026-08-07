import { STORAGE_KEYS, PROFILES, THEMES } from '@/constants';

export const AppInitializer = {
  init: () => {
    console.log('App Initializing...');
    
    // Ensure default theme is saved
    if (!localStorage.getItem(STORAGE_KEYS.THEME)) {
      localStorage.setItem(STORAGE_KEYS.THEME, THEMES.SYSTEM);
    }
    
    // Ensure default profile is saved - removed to allow onboarding to set it
    
    console.log('App Initialized successfully.');
  }
};

export default AppInitializer;
