import { PROFILES } from '@/constants';

/**
 * Reusable Reports & Analytics Configuration & Datasets
 *
 * Centralizes profile-specific analytics metrics, mock chart datasets,
 * tab visibility configurations, export history, and report settings.
 */

// Colors matching Claymorphism Design Tokens
export const Colors = {
  primary: '#7C3AED',
  secondary: '#8B5CF6',
  accent: '#EC4899',
  success: '#10B981',
  warning: '#F59E0B',
  danger: '#EF4444',
  info: '#3B82F6',
  muted: '#94A3B8',
};

// Centralized Reusable Mock Datasets for Recharts
export const mockDatasets = {
  // Income vs Expenses (Monthly)
  incomeVsExpenses: [
    { month: 'Jan', income: 45000, expenses: 28000, savings: 17000 },
    { month: 'Feb', income: 52000, expenses: 31000, savings: 21000 },
    { month: 'Mar', income: 48000, expenses: 29500, savings: 18500 },
    { month: 'Apr', income: 61000, expenses: 34000, savings: 27000 },
    { month: 'May', income: 55000, expenses: 30000, savings: 25000 },
    { month: 'Jun', income: 68000, expenses: 36000, savings: 32000 },
    { month: 'Jul', income: 72000, expenses: 38500, savings: 33500 },
    { month: 'Aug', income: 85000, expenses: 42750, savings: 42250 },
  ],

  // Expense Categories (Donut/Pie)
  expenseCategories: [
    { name: 'Rent & Living', value: 18000, color: '#7C3AED' },
    { name: 'Groceries & Dining', value: 8500, color: '#EF4444' },
    { name: 'Utilities & Bills', value: 6400, color: '#F59E0B' },
    { name: 'Insurance & Taxes', value: 5650, color: '#10B981' },
    { name: 'Commute & Travel', value: 4200, color: '#3B82F6' },
  ],

  // Daily Spending (Last 7 Days)
  dailySpending: [
    { day: 'Mon', income: 0, expense: 1200 },
    { day: 'Tue', income: 15000, expense: 850 },
    { day: 'Wed', income: 0, expense: 2400 },
    { day: 'Thu', income: 0, expense: 650 },
    { day: 'Fri', income: 8000, expense: 3100 },
    { day: 'Sat', income: 0, expense: 4500 },
    { day: 'Sun', income: 0, expense: 1800 },
  ],

  // Weekly Comparison (Last 4 Weeks)
  weeklyPerformance: [
    { week: 'Week 1', budget: 22000, spent: 18500, saved: 3500 },
    { week: 'Week 2', budget: 22000, spent: 21000, saved: 1000 },
    { week: 'Week 3', budget: 22000, spent: 17200, saved: 4800 },
    { week: 'Week 4', budget: 22000, spent: 19800, saved: 2200 },
  ],

  // Annual Performance (5-Year Trend)
  annualGrowth: [
    { year: '2022', revenue: 380000, expenses: 240000, netWorth: 140000 },
    { year: '2023', revenue: 520000, expenses: 310000, netWorth: 350000 },
    { year: '2024', revenue: 690000, expenses: 390000, netWorth: 650000 },
    { year: '2025', revenue: 880000, expenses: 460000, netWorth: 1070000 },
    { year: '2026', revenue: 1120000, expenses: 530000, netWorth: 1660000 },
  ],

  // Asset Allocation (Radar / Pie)
  assetAllocation: [
    { subject: 'Mutual Funds', A: 45, fullMark: 100 },
    { subject: 'Direct Stocks', A: 35, fullMark: 100 },
    { subject: 'Fixed Deposits', A: 10, fullMark: 100 },
    { subject: 'Gold', A: 5, fullMark: 100 },
    { subject: 'Cash Reserves', A: 5, fullMark: 100 },
  ],

  // Investment Growth (Area Chart)
  investmentGrowth: [
    { period: 'Q1 25', portfolio: 180000, benchmark: 175000 },
    { period: 'Q2 25', portfolio: 210000, benchmark: 198000 },
    { period: 'Q3 25', portfolio: 245000, benchmark: 225000 },
    { period: 'Q4 25', portfolio: 278000, benchmark: 250000 },
    { period: 'Q1 26', portfolio: 312000, benchmark: 280000 },
  ],

  // Goals Analytics
  goalsAnalytics: [
    { goal: 'Emergency Fund', progress: 80, target: 150000, current: 120000, category: 'Safety' },
    { goal: 'Laptop Purchase', progress: 100, target: 80000, current: 80000, category: 'Tech' },
    { goal: 'Home Downpayment', progress: 40, target: 1000000, current: 400000, category: 'Real Estate' },
    { goal: 'Vacation Trip', progress: 65, target: 60000, current: 39000, category: 'Leisure' },
  ],
};

// Profile-Specific Reports Configuration
export const reportsConfig = {
  [PROFILES.STUDENT]: {
    focusMetrics: [
      { title: 'Total Allowance', value: '₹5,000', change: '+0%', status: 'Stable', icon: 'Wallet' },
      { title: 'Monthly Expenses', value: '₹4,550', change: '-5.2%', status: 'Under Budget', icon: 'ShoppingBag' },
      { title: 'Scholarship / Stipend', value: '₹4,000', change: '+12.5%', status: 'Active', icon: 'Award' },
      { title: 'Savings Balance', value: '₹12,450', change: '+18.4%', status: 'Growing', icon: 'PiggyBank' },
    ],
    highlights: [
      { text: 'You stayed within budget limits for 3 consecutive months.', type: 'positive' },
      { text: 'Book purchases were 15% lower than semester allocation.', type: 'positive' },
    ],
  },
  [PROFILES.PROFESSIONAL]: {
    focusMetrics: [
      { title: 'Gross Income', value: '₹97,000', change: '+8.3%', status: 'On Target', icon: 'Briefcase' },
      { title: 'Monthly Expenses', value: '₹42,750', change: '-3.1%', status: 'Healthy Margin', icon: 'CreditCard' },
      { title: 'Liquid Savings', value: '₹54,250', change: '+14.2%', status: 'High Yield', icon: 'TrendingUp' },
      { title: 'Portfolio Net Worth', value: '₹3,12,000', change: '+14.1%', status: 'Optimal', icon: 'Gem' },
    ],
    highlights: [
      { text: 'Savings rate reached 55% of monthly salary income.', type: 'positive' },
      { text: 'Equity portfolio outperformed benchmark by +2.8%.', type: 'positive' },
    ],
  },
  [PROFILES.BUSINESS]: {
    focusMetrics: [
      { title: 'Gross Revenue', value: '₹4,85,000', change: '+15.4%', status: 'Strong', icon: 'BarChart' },
      { title: 'Operating OPEX', value: '₹2,75,000', change: '-4.0%', status: 'Controlled', icon: 'Boxes' },
      { title: 'Net Cash Surplus', value: '₹2,10,000', change: '+22.1%', status: 'High Cushion', icon: 'RefreshCw' },
      { title: 'Corporate Reserves', value: '₹6,45,000', change: '+11.8%', status: 'Liquid', icon: 'Landmark' },
    ],
    highlights: [
      { text: 'Operating expenses decreased by 4% through payroll optimization.', type: 'positive' },
      { text: 'Receivables aging average reduced to 18 days.', type: 'positive' },
    ],
  },
};

export const getReportsConfig = (profileName) => {
  return reportsConfig[profileName] || reportsConfig[PROFILES.STUDENT];
};

export default reportsConfig;
