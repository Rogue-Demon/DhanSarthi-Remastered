import { PROFILES } from '@/constants';

/**
 * AI Financial Advisor Configuration
 *
 * Centralizes profile-specific prompts, welcome messages, insight placeholders,
 * quick actions, and template metadata. Components read from this config
 * instead of hardcoding profile checks.
 */
export const aiAdvisorConfig = {
  [PROFILES.STUDENT]: {
    welcome: {
      greeting: 'Hey Shreyanshu! 👋',
      headline: 'Your AI-powered pocket finance mentor',
      description: 'Ask me anything about budgeting, saving strategies, scholarship planning, or building healthy financial habits as a student.',
    },
    suggestedPrompts: [
      { text: 'Help me save more money this month', icon: 'PiggyBank', category: 'Saving' },
      { text: 'Can I afford this purchase?', icon: 'ShoppingBag', category: 'Budgeting' },
      { text: 'Create my monthly student budget', icon: 'Calculator', category: 'Budgeting' },
      { text: 'How do micro-SIPs work for students?', icon: 'TrendingUp', category: 'Investments' },
    ],
    insights: [
      { title: 'Budget Health', value: 'On Track', icon: 'Heart', color: '#10B981' },
      { title: 'Savings Goal', value: '₹450 left', icon: 'Target', color: '#7C3AED' },
      { title: 'Spending Trend', value: 'Steady', icon: 'TrendingUp', color: '#3B82F6' },
    ],
    quickActions: [
      { label: 'Budget Review', icon: 'Calculator' },
      { label: 'Savings Tips', icon: 'Lightbulb' },
      { label: 'Goal Planning', icon: 'Target' },
    ],
  },
  [PROFILES.PROFESSIONAL]: {
    welcome: {
      greeting: 'Welcome back, Shreyanshu',
      headline: 'Your AI wealth management co-pilot',
      description: 'Analyze your portfolio, optimize taxes, plan retirement projections, or review investment strategies with data-driven insights.',
    },
    suggestedPrompts: [
      { text: 'How can I reduce my monthly expenses?', icon: 'TrendingDown', category: 'Expenses' },
      { text: 'Review my current investment strategy', icon: 'BarChart2', category: 'Investments' },
      { text: 'Estimate my retirement corpus at age 60', icon: 'Landmark', category: 'Retirement' },
      { text: 'Optimize my Section 80C tax deductions', icon: 'Percent', category: 'Tax' },
    ],
    insights: [
      { title: 'Portfolio Return', value: '+14.1% YTD', icon: 'TrendingUp', color: '#10B981' },
      { title: 'Tax Savings', value: '₹12,400 saved', icon: 'Percent', color: '#7C3AED' },
      { title: 'Net Worth Trend', value: 'Growing', icon: 'BarChart', color: '#3B82F6' },
    ],
    quickActions: [
      { label: 'Investment Review', icon: 'BarChart2' },
      { label: 'Tax Planner', icon: 'Percent' },
      { label: 'Financial Health', icon: 'Activity' },
      { label: 'Goal Planning', icon: 'Target' },
    ],
  },
  [PROFILES.BUSINESS]: {
    welcome: {
      greeting: 'Good afternoon, Shreyanshu',
      headline: 'Your AI-powered enterprise financial analyst',
      description: 'Analyze cash flows, optimize payroll overheads, forecast revenue projections, or review corporate reserve allocations.',
    },
    suggestedPrompts: [
      { text: 'Improve my business cash flow this quarter', icon: 'RefreshCw', category: 'Cash Flow' },
      { text: 'Reduce operating expenses by 15%', icon: 'TrendingDown', category: 'OPEX' },
      { text: 'Analyze quarterly revenue trends', icon: 'BarChart', category: 'Revenue' },
      { text: 'Forecast next quarter payroll budget', icon: 'Users', category: 'Payroll' },
    ],
    insights: [
      { title: 'Cash Ratio', value: '2.5x Healthy', icon: 'Activity', color: '#10B981' },
      { title: 'OPEX Margin', value: '₹2.75L', icon: 'TrendingDown', color: '#EF4444' },
      { title: 'Revenue Target', value: '92% achieved', icon: 'Target', color: '#7C3AED' },
    ],
    quickActions: [
      { label: 'Cash Flow Review', icon: 'RefreshCw' },
      { label: 'OPEX Analysis', icon: 'TrendingDown' },
      { label: 'Revenue Forecast', icon: 'BarChart' },
    ],
  },
};

/**
 * Prompt Library Categories — shared across all profiles
 */
export const promptLibrary = [
  {
    category: 'Budgeting',
    icon: 'Calculator',
    color: '#7C3AED',
    prompts: [
      'Create a monthly budget plan',
      'How much should I allocate to savings?',
      'Review my spending categories',
    ],
  },
  {
    category: 'Saving',
    icon: 'PiggyBank',
    color: '#10B981',
    prompts: [
      'Best savings strategies for beginners',
      'How to build an emergency fund',
      'Compare savings account interest rates',
    ],
  },
  {
    category: 'Investments',
    icon: 'TrendingUp',
    color: '#3B82F6',
    prompts: [
      'Explain mutual funds vs direct stocks',
      'Should I start a SIP?',
      'What is a good asset allocation?',
    ],
  },
  {
    category: 'Tax',
    icon: 'Percent',
    color: '#F59E0B',
    prompts: [
      'Optimize my tax deductions',
      'Explain Section 80C benefits',
      'Tax implications of selling stocks',
    ],
  },
  {
    category: 'Loans',
    icon: 'Handshake',
    color: '#EF4444',
    prompts: [
      'Should I prepay my home loan?',
      'Compare loan refinancing options',
      'Education loan repayment strategies',
    ],
  },
  {
    category: 'Business',
    icon: 'Building',
    color: '#6366F1',
    prompts: [
      'Improve business cash flow',
      'Reduce payroll overheads',
      'Forecast quarterly revenue',
    ],
  },
];

/**
 * AI Templates — reusable prompt templates
 */
export const aiTemplates = [
  { id: 'budget-planner', title: 'Budget Planner', desc: 'Create a comprehensive monthly budget based on your income and goals.', icon: 'Calculator', color: '#7C3AED' },
  { id: 'investment-review', title: 'Investment Review', desc: 'Analyze your current portfolio allocation and suggest optimizations.', icon: 'BarChart2', color: '#3B82F6' },
  { id: 'expense-analysis', title: 'Expense Analysis', desc: 'Deep-dive into your spending patterns and identify savings opportunities.', icon: 'ArrowDownLeft', color: '#EF4444' },
  { id: 'savings-plan', title: 'Savings Plan', desc: 'Build a structured savings roadmap to reach your financial goals faster.', icon: 'PiggyBank', color: '#10B981' },
  { id: 'debt-reduction', title: 'Debt Reduction', desc: 'Create a debt payoff strategy using avalanche or snowball methods.', icon: 'Handshake', color: '#F59E0B' },
  { id: 'emergency-fund', title: 'Emergency Fund', desc: 'Calculate your ideal emergency fund size and build a contribution plan.', icon: 'Shield', color: '#6366F1' },
  { id: 'retirement-planning', title: 'Retirement Planning', desc: 'Estimate your retirement corpus and required monthly contributions.', icon: 'Landmark', color: '#EC4899' },
  { id: 'business-cashflow', title: 'Business Cash Flow', desc: 'Analyze inflow-outflow patterns and optimize working capital.', icon: 'RefreshCw', color: '#14B8A6' },
];

/**
 * Static placeholder conversations for the history panel
 */
export const placeholderConversations = [
  { id: '1', title: 'Monthly Budget Planning', preview: 'Let me help you create a structured monthly budget...', date: 'Today', pinned: true, favorite: true },
  { id: '2', title: 'Investment Portfolio Review', preview: 'Your current allocation is 60% equity, 30% debt...', date: 'Yesterday', pinned: false, favorite: true },
  { id: '3', title: 'Tax Savings Strategy', preview: 'Based on your salary structure, you can save up to...', date: '3 days ago', pinned: false, favorite: false },
  { id: '4', title: 'Emergency Fund Calculator', preview: 'An ideal emergency fund should cover 6 months of...', date: '1 week ago', pinned: true, favorite: false },
  { id: '5', title: 'SIP vs Lump Sum Analysis', preview: 'For long-term wealth creation, SIP offers rupee cost...', date: '2 weeks ago', pinned: false, favorite: false },
];

/**
 * Static placeholder chat messages for demo
 */
export const placeholderMessages = [
  {
    id: 'm1',
    role: 'user',
    content: 'Can you help me create a monthly budget? I earn ₹85,000 per month.',
    timestamp: '10:30 AM',
  },
  {
    id: 'm2',
    role: 'assistant',
    content: "Absolutely! Based on your income of ₹85,000, here's a suggested allocation using the 50/30/20 rule:\n\n**Needs (50%) — ₹42,500**\n• Rent & Utilities: ₹18,000\n• Groceries: ₹8,000\n• Transport: ₹4,500\n• Insurance: ₹6,000\n• Bills: ₹6,000\n\n**Wants (30%) — ₹25,500**\n• Dining & Entertainment: ₹8,000\n• Shopping: ₹7,500\n• Subscriptions: ₹2,000\n• Personal Care: ₹4,000\n• Miscellaneous: ₹4,000\n\n**Savings & Investments (20%) — ₹17,000**\n• Emergency Fund: ₹5,000\n• SIP Investments: ₹7,000\n• PPF/NPS: ₹5,000\n\nWould you like me to adjust any category?",
    timestamp: '10:31 AM',
  },
  {
    id: 'm3',
    role: 'user',
    content: 'That looks great! Can you increase the savings portion to 25%?',
    timestamp: '10:32 AM',
  },
  {
    id: 'm4',
    role: 'assistant',
    content: "Great decision! Increasing savings to 25% (₹21,250) would look like:\n\n**Updated Savings & Investments (25%) — ₹21,250**\n• Emergency Fund: ₹5,000\n• SIP Investments: ₹10,000 (+₹3,000)\n• PPF/NPS: ₹6,250 (+₹1,250)\n\nTo accommodate this, I'd suggest reducing **Wants** to 25% (₹21,250):\n• Dining & Entertainment: ₹6,500 (-₹1,500)\n• Shopping: ₹6,000 (-₹1,500)\n• Other categories stay the same.\n\nThis puts you on track to build a ₹2.5L emergency fund in ~4 years and a strong retirement corpus. Shall I create a detailed savings plan?",
    timestamp: '10:33 AM',
  },
];

export const getAIAdvisorConfig = (profileName) => {
  return aiAdvisorConfig[profileName] || aiAdvisorConfig[PROFILES.STUDENT];
};

export default aiAdvisorConfig;
