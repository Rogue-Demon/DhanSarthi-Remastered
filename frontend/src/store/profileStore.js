import { create } from 'zustand';
import { STORAGE_KEYS, PROFILES } from '@/constants';

/**
 * Profile Store
 *
 * Manages the active user profile and onboarding completion state.
 * Persists to localStorage for session continuity.
 * Designed for minimal changes when integrating a real backend.
 */
export const useProfileStore = create((set, get) => ({
  // Current active profile — null until user completes onboarding
  profile: localStorage.getItem(STORAGE_KEYS.PROFILE) || null,

  // Whether the onboarding flow has been completed
  onboardingComplete:
    localStorage.getItem(STORAGE_KEYS.ONBOARDING_COMPLETE) === 'true',

  /**
   * Set the active profile.
   * Updates both Zustand state and localStorage.
   */
  setProfile: (profile) => {
    localStorage.setItem(STORAGE_KEYS.PROFILE, profile);
    set({ profile });
  },

  /**
   * Mark onboarding as completed.
   * Called after user confirms their profile selection.
   */
  completeOnboarding: () => {
    localStorage.setItem(STORAGE_KEYS.ONBOARDING_COMPLETE, 'true');
    set({ onboardingComplete: true });
  },

  /**
   * Reset onboarding state.
   * Useful for testing or allowing the user to re-onboard.
   */
  resetOnboarding: () => {
    localStorage.removeItem(STORAGE_KEYS.ONBOARDING_COMPLETE);
    localStorage.removeItem(STORAGE_KEYS.PROFILE);
    set({ onboardingComplete: false, profile: null });
  },

  /**
   * Check if the user has a profile selected.
   */
  hasProfile: () => {
    return !!get().profile;
  },
}));

export default useProfileStore;
