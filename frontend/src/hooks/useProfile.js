import { useProfileStore } from '@/store';
import { getProfileConfig } from '@/config/profiles.config';

/**
 * useProfile hook
 *
 * Provides profile state, actions, and resolved profile configuration.
 * Single source of truth for any component needing profile context.
 */
export const useProfile = () => {
  const {
    profile,
    onboardingComplete,
    setProfile,
    completeOnboarding,
    resetOnboarding,
    hasProfile,
  } = useProfileStore();

  // Resolved config for the current profile (null-safe)
  const profileConfig = profile ? getProfileConfig(profile) : null;

  return {
    profile,
    profileConfig,
    onboardingComplete,
    setProfile,
    completeOnboarding,
    resetOnboarding,
    hasProfile,
  };
};

export default useProfile;
