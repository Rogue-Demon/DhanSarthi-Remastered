import { PROFILES } from '@/constants';

/**
 * Dashboard Layout Configuration
 * Defines widget visibility, order, spacing rules, size spans (12-column system),
 * and future permission/feature flags placeholders for each user profile.
 */
export const dashboardConfig = {
  [PROFILES.STUDENT]: {
    bannerMessage: "Let's build smarter saving habits.",
    widgets: [
      {
        id: 'student-allowance',
        size: 'md', // col-span-6
        order: 1,
        visible: true,
        permissions: ['read', 'write'],
        featureFlags: ['student_allowance_tracker'],
      },
      {
        id: 'student-savings',
        size: 'md', // col-span-6
        order: 2,
        visible: true,
        permissions: ['read', 'write'],
        featureFlags: ['student_savings_goals'],
      },
      {
        id: 'student-budget',
        size: 'lg', // col-span-8
        order: 3,
        visible: true,
        permissions: ['read'],
        featureFlags: ['student_budget_manager'],
      },
      {
        id: 'student-education',
        size: 'sm', // col-span-4
        order: 4,
        visible: true,
        permissions: ['read'],
        featureFlags: ['student_education_logs'],
      },
      {
        id: 'student-goals',
        size: 'xl', // col-span-12 (full width)
        order: 5,
        visible: true,
        permissions: ['read'],
        featureFlags: ['student_milestones_streaks'],
      },
    ],
  },
  [PROFILES.PROFESSIONAL]: {
    bannerMessage: 'Take control of your financial future.',
    widgets: [
      {
        id: 'professional-salary',
        size: 'sm', // col-span-4
        order: 1,
        visible: true,
        permissions: ['read'],
        featureFlags: ['prof_salary_tracker'],
      },
      {
        id: 'professional-expenses',
        size: 'sm', // col-span-4
        order: 2,
        visible: true,
        permissions: ['read'],
        featureFlags: ['prof_expense_categorizer'],
      },
      {
        id: 'professional-networth',
        size: 'sm', // col-span-4
        order: 3,
        visible: true,
        permissions: ['read'],
        featureFlags: ['prof_networth_live'],
      },
      {
        id: 'professional-investments',
        size: 'md', // col-span-6
        order: 4,
        visible: true,
        permissions: ['read'],
        featureFlags: ['prof_investments_portfolio'],
      },
      {
        id: 'professional-assets',
        size: 'md', // col-span-6
        order: 5,
        visible: true,
        permissions: ['read'],
        featureFlags: ['prof_assets_manager'],
      },
    ],
  },
  [PROFILES.BUSINESS]: {
    bannerMessage: 'Run your business with financial clarity.',
    widgets: [
      {
        id: 'business-revenue',
        size: 'md', // col-span-6
        order: 1,
        visible: true,
        permissions: ['read'],
        featureFlags: ['biz_revenue_pipeline'],
      },
      {
        id: 'business-profit',
        size: 'md', // col-span-6
        order: 2,
        visible: true,
        permissions: ['read'],
        featureFlags: ['biz_profit_margins'],
      },
      {
        id: 'business-cashflow',
        size: 'xl', // col-span-12
        order: 3,
        visible: true,
        permissions: ['read'],
        featureFlags: ['biz_cashflow_statements'],
      },
      {
        id: 'business-payroll',
        size: 'md', // col-span-6
        order: 4,
        visible: true,
        permissions: ['read'],
        featureFlags: ['biz_payroll_manager'],
      },
      {
        id: 'business-inventory',
        size: 'md', // col-span-6
        order: 5,
        visible: true,
        permissions: ['read'],
        featureFlags: ['biz_stock_control'],
      },
    ],
  },
};

/**
 * Get active widgets for a profile
 * @param {string} profileName - Selected user profile name
 * @returns {Array} List of visible widget configurations, ordered
 */
export const getActiveWidgets = (profileName) => {
  const config = dashboardConfig[profileName];
  if (!config) return [];

  return config.widgets
    .filter((w) => w.visible)
    .sort((a, b) => a.order - b.order);
};

export default dashboardConfig;
