import { PROFILES } from '@/constants';

/**
 * Reusable Finance Module Configuration
 *
 * Centralizes all profile-specific content, categories, charts metadata, initial status values,
 * and icons to prevent hardcoded profile checks in individual UI components.
 */
export const financeConfig = {
  [PROFILES.STUDENT]: {
    income: {
      title: 'Student Allowances & Stipends',
      items: [
        { label: 'Monthly Pocket Allowance', value: '₹5,000', icon: 'Wallet', desc: 'Parental stipend' },
        { label: 'Academic Scholarships', value: '₹2,500', icon: 'Award', desc: 'Merit-based credit' },
        { label: 'Part-Time Tutoring', value: '₹1,500', icon: 'BookOpen', desc: 'Side coaching gig' },
      ],
    },
    expenses: {
      title: 'Student Expenses Tracker',
      items: [
        { category: 'Tuition & Books', spent: '₹2,100', budget: '₹3,000', icon: 'GraduationCap', color: '#8B5CF6' },
        { category: 'Food & Cafeteria', spent: '₹1,200', budget: '₹1,500', icon: 'Coffee', color: '#EC4899' },
        { category: 'Local Transport', spent: '₹450', budget: '₹600', icon: 'Car', color: '#3B82F6' },
        { category: 'Social & Entertainment', spent: '₹800', budget: '₹1,000', icon: 'Play', color: '#10B981' },
      ],
    },
    assets: {
      title: 'Student Capital Assets',
      items: [
        { name: 'Goal Savings Deposits', value: '₹12,450', icon: 'PiggyBank', type: 'Savings Account' },
        { name: 'Study Laptop (MacBook)', value: '₹35,000', icon: 'Laptop', type: 'Gadget Equity' },
        { name: 'Mutual Fund SIP Balance', value: '₹4,500', icon: 'TrendingUp', type: 'Micro Investments' },
      ],
    },
    liabilities: {
      title: 'Student Active Liabilities',
      items: [
        { name: 'Education Loan (State Bank)', value: '₹1,50,000', rate: '8.5% p.a.', icon: 'GraduationCap', due: 'Repayment post graduation' },
        { name: 'Borrowed from Friends (Peer)', value: '₹800', rate: 'Interest-free', icon: 'Users', due: 'Due in 14 days' },
      ],
    },
    budget: {
      allowance: '₹5,000',
      spent: '₹4,550',
      remaining: '₹450',
      progress: 91,
      target: '₹4,000',
      status: 'Tight Budget',
    },
    cashFlow: {
      income: '₹9,000',
      expense: '₹4,550',
      netFlow: '₹4,450',
      receivables: '₹1,500',
      payables: '₹800',
    },
    goals: [
      { name: 'Buy Semester Books', current: 1500, target: 2000, due: 'Oct 2026', color: '#10B981', icon: 'BookOpen' },
      { name: 'Emergency Support Fund', current: 5000, target: 10000, due: 'Dec 2026', color: '#8B5CF6', icon: 'Shield' },
    ],
    insights: [
      { text: "Your tuition expense is fully logged. You're within standard budget margins.", type: 'positive' },
      { text: 'Scholarships contribution is expected next week.', type: 'info' },
    ],
  },
  [PROFILES.PROFESSIONAL]: {
    income: {
      title: 'Professional Salaries & Freelance',
      items: [
        { label: 'Monthly Corporate Salary', value: '₹85,000', icon: 'Briefcase', desc: 'Primary job' },
        { label: 'UI/UX Design Freelancing', value: '₹12,000', icon: 'Laptop', desc: 'Retainer client' },
        { label: 'Annual Bonus Accrual', value: '₹5,000', icon: 'TrendingUp', desc: 'Quarterly target share' },
      ],
    },
    expenses: {
      title: 'Professional Household Expenses',
      items: [
        { category: 'House Rent & Maintenance', spent: '₹18,000', budget: '₹20,000', icon: 'Home', color: '#7C3AED' },
        { category: 'Groceries & Dining', spent: '₹8,500', budget: '₹10,000', icon: 'ShoppingBag', color: '#EF4444' },
        { category: 'Commute & Petrol', spent: '₹4,200', budget: '₹5,000', icon: 'Car', color: '#3B82F6' },
        { category: 'Utilities & WiFi Bills', spent: '₹6,400', budget: '₹7,500', icon: 'Activity', color: '#F59E0B' },
        { category: 'Life & Health Insurance', spent: '₹5,650', budget: '₹6,000', icon: 'HeartHandshake', color: '#10B981' },
      ],
    },
    assets: {
      title: 'Professional Portfolio Assets',
      items: [
        { name: 'Liquid Savings Deposits', value: '₹54,600', icon: 'PiggyBank', type: 'Checking Account' },
        { name: 'Mutual Funds & SIPs', value: '₹1,40,400', icon: 'TrendingUp', type: 'Market Portfolio' },
        { name: 'Direct Stocks Equity', value: '₹1,09,200', icon: 'BarChart', type: 'Trading Capital' },
        { name: 'Gold / Sovereign Bonds', value: '₹31,200', icon: 'Gem', type: 'SGB Bonds' },
      ],
    },
    liabilities: {
      title: 'Professional Loans & Liabilities',
      items: [
        { name: 'Car Loan (Axis Bank EMI)', value: '₹1,20,000', rate: '9.2% p.a.', icon: 'Car', due: '₹4,500 due on 12th Aug' },
        { name: 'Credit Card Outstanding', value: '₹12,200', rate: 'Deferred', icon: 'CreditCard', due: '₹12,200 due on 15th Aug' },
      ],
    },
    budget: {
      allowance: '₹95,000',
      spent: '₹42,750',
      remaining: '₹52,250',
      progress: 45,
      target: '₹50,000',
      status: 'Healthy Budget',
    },
    cashFlow: {
      income: '₹97,000',
      expense: '₹42,750',
      netFlow: '₹54,250',
      receivables: '₹12,000',
      payables: '₹16,700',
    },
    goals: [
      { name: 'Emergency Cushion Fund', current: 120000, target: 150000, due: 'Dec 2026', color: '#10B981', icon: 'Shield' },
      { name: 'Home Purchase Downpayment', current: 400000, target: 1000000, due: 'Dec 2028', color: '#7C3AED', icon: 'Home' },
    ],
    insights: [
      { text: "Your monthly spend is well-contained under 50% limit. High savings yield expected.", type: 'positive' },
      { text: 'Tax exemption threshold is close to limit. Optimize deductions.', type: 'warning' },
    ],
  },
  [PROFILES.BUSINESS]: {
    income: {
      title: 'Corporate Inflow & Services',
      items: [
        { label: 'Product Sales Gross', value: '₹3,50,000', icon: 'Boxes', desc: 'Direct warehouse deliveries' },
        { label: 'Consulting Retainers', value: '₹1,10,000', icon: 'Briefcase', desc: 'Contract advisory' },
        { label: 'SaaS Software Licenses', value: '₹25,000', icon: 'Laptop', desc: 'Subscription renewals' },
      ],
    },
    expenses: {
      title: 'Operational Overheads (OPEX)',
      items: [
        { category: 'Staff Salaries (Payroll)', spent: '₹95,000', budget: '₹1,00,000', icon: 'Users', color: '#7C3AED' },
        { category: 'Warehouse & Office Rental', spent: '₹49,500', budget: '₹50,000', icon: 'Home', color: '#EF4444' },
        { category: 'Stock & Inventory purchases', spent: '₹80,000', budget: '₹1,00,000', icon: 'Boxes', color: '#F59E0B' },
        { category: 'Marketing & Ad Campaigns', spent: '₹35,000', budget: '₹40,000', icon: 'Megaphone', color: '#10B981' },
        { category: 'Hosting Servers & SaaS tools', spent: '₹15,500', budget: '₹20,000', icon: 'Server', color: '#3B82F6' },
      ],
    },
    assets: {
      title: 'Corporate Asset Ledger',
      items: [
        { name: 'Finished Product Inventory', value: '₹2,40,000', icon: 'Boxes', type: 'Stock In Hand' },
        { name: 'Office Server Equipment', value: '₹1,85,000', icon: 'Server', type: 'Hardware Assets' },
        { name: 'Bank Reserves (HDFC Liquid)', value: '₹2,10,000', icon: 'PiggyBank', type: 'Corporate Savings' },
        { name: 'Receivables Invoices pending', value: '₹1,17,000', icon: 'ArrowRight', type: 'Outstanding Client Fees' },
      ],
    },
    liabilities: {
      title: 'Corporate Liability & Payables',
      items: [
        { name: 'Vendor Purchase Orders', value: '₹49,500', rate: 'Interest-free', icon: 'ShoppingCart', due: 'Net-30 payment due 20th Aug' },
        { name: 'Corporate Line of Credit', value: '₹2,50,000', rate: '12.4% p.a.', icon: 'Building', due: 'Monthly recurring interest' },
        { name: 'GST / Tax liabilities accrued', value: '₹34,500', rate: 'Statutory', icon: 'Percent', due: 'GST return due 20th Aug' },
      ],
    },
    budget: {
      allowance: '₹3,10,000',
      spent: '₹2,75,000',
      remaining: '₹35,000',
      progress: 88,
      target: '₹2,50,000',
      status: 'Review Budget',
    },
    cashFlow: {
      income: '₹4,85,000',
      expense: '₹2,75,000',
      netFlow: '₹2,10,000',
      receivables: '₹1,17,000',
      payables: '₹84,000',
    },
    goals: [
      { name: 'Operating Overhead Cut', current: 15, target: 20, due: 'Dec 2026', color: '#10B981', icon: 'TrendingDown' },
      { name: 'Sales Revenue target', current: 55.8, target: 60, due: 'Mar 2027', color: '#7C3AED', icon: 'IndianRupee' },
    ],
    insights: [
      { text: 'Cash ratio remains strong at 2.5. Good liquidity cushioning.', type: 'positive' },
      { text: 'Invoices collection delayed by 5 days on average. Set reminders.', type: 'warning' },
    ],
  },
};

/**
 * Resolve finance configuration for a profile
 * @param {string} profileName - Selected user profile name
 * @returns {object|null} Config details
 */
export const getFinanceConfig = (profileName) => {
  return financeConfig[profileName] || null;
};

export default financeConfig;
