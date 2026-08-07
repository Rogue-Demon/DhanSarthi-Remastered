import { PROFILES } from '@/constants';

/**
 * Centralized profile configuration
 * All profile-specific content lives here for easy maintenance
 * and future backend integration.
 */
export const profilesConfig = {
  [PROFILES.STUDENT]: {
    id: 'student',
    name: PROFILES.STUDENT,
    label: 'Student',
    icon: 'GraduationCap',
    color: '#8B5CF6',
    gradient: 'linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%)',
    description: 'Smart financial habits for students and learners.',
    shortDescription: 'Track allowances, scholarships & build savings goals.',
    welcomeMessage: "Let's build smarter saving habits.",
    features: [
      'Allowance Tracking',
      'Scholarship Management',
      'Savings Goals',
      'Budget Planning',
      'Education Expenses',
      'Savings Streaks',
    ],
    focusAreas: [
      'Allowance',
      'Scholarships',
      'Savings',
      'Budget Planning',
      'Education Expenses',
      'Savings Goals',
    ],
  },
  [PROFILES.PROFESSIONAL]: {
    id: 'professional',
    name: PROFILES.PROFESSIONAL,
    label: 'Working Professional',
    icon: 'Briefcase',
    color: '#7C3AED',
    gradient: 'linear-gradient(135deg, #7C3AED 0%, #4F46E5 100%)',
    description: 'Complete financial overview for working professionals.',
    shortDescription: 'Manage salary, expenses, investments & tax planning.',
    welcomeMessage: 'Take control of your financial future.',
    features: [
      'Salary Management',
      'Expense Tracking',
      'Asset Overview',
      'Liability Tracking',
      'Investment Portfolio',
      'Tax Overview',
    ],
    focusAreas: [
      'Salary',
      'Expenses',
      'Assets',
      'Liabilities',
      'Investments',
      'Tax Overview',
    ],
  },
  [PROFILES.BUSINESS]: {
    id: 'business',
    name: PROFILES.BUSINESS,
    label: 'Business',
    icon: 'Building2',
    color: '#4F46E5',
    gradient: 'linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%)',
    description: 'Enterprise-grade financial management for businesses.',
    shortDescription: 'Revenue, cash flow, payroll & business analytics.',
    welcomeMessage: 'Run your business with financial clarity.',
    features: [
      'Revenue Tracking',
      'Profit Analysis',
      'Cash Flow Management',
      'Payroll Overview',
      'Inventory Tracking',
      'Business Analytics',
    ],
    focusAreas: [
      'Revenue',
      'Profit',
      'Cash Flow',
      'Payroll',
      'Inventory',
      'Business Analytics',
    ],
  },
};

/**
 * Get profile config by profile name
 * @param {string} profileName - one of PROFILES values
 * @returns {object} profile config
 */
export const getProfileConfig = (profileName) => {
  return profilesConfig[profileName] || profilesConfig[PROFILES.STUDENT];
};

/**
 * Get all profiles as an ordered array
 * @returns {Array} ordered profile configs
 */
export const getProfilesList = () => {
  return [
    profilesConfig[PROFILES.STUDENT],
    profilesConfig[PROFILES.PROFESSIONAL],
    profilesConfig[PROFILES.BUSINESS],
  ];
};

export default profilesConfig;
