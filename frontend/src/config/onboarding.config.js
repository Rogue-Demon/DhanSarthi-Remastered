/**
 * Onboarding configuration
 * Centralized configuration for the onboarding flow.
 */
export const onboardingConfig = {
  steps: [
    { id: 'welcome', label: 'Welcome', path: '/onboarding' },
    { id: 'select-profile', label: 'Select Profile', path: '/select-profile' },
    { id: 'confirmation', label: 'Confirmation', path: '/select-profile' },
  ],

  welcome: {
    heading: 'Your AI-Powered Financial Companion',
    subheading: 'Smart. Personal. Effortless.',
    description:
      'धनSarthi adapts to your financial needs — whether you\'re a student, working professional, or business owner. Get personalized insights, budgets, and AI-powered advice.',
    ctaText: 'Get Started',
  },

  confirmation: {
    heading: 'You\'re All Set!',
    subheading: 'Your dashboard is being personalized.',
    ctaText: 'Continue to Dashboard',
    backText: 'Change Profile',
  },
};

export default onboardingConfig;
