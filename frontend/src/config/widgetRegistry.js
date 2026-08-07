import React from 'react';
import * as LucideIcons from 'lucide-react';

/**
 * Centralized Widget Registry
 * Maps unique widget IDs to their configuration, metadata, and component definition.
 * Supports future widget expansions seamlessly without layout modifications.
 */
export const widgetRegistry = {
  // --- Student Widgets ---
  'student-allowance': {
    id: 'student-allowance',
    title: 'Monthly Allowance',
    icon: 'Wallet',
    description: 'Track pocket money, monthly stipends, and allowance distributions.',
    color: '#8B5CF6',
  },
  'student-savings': {
    id: 'student-savings',
    title: 'Savings Goals',
    icon: 'PiggyBank',
    description: 'Monitor targets for gadgets, books, travel, and personal funds.',
    color: '#EC4899',
  },
  'student-education': {
    id: 'student-education',
    title: 'Education Expenses',
    icon: 'GraduationCap',
    description: 'Log tuition fees, course materials, subscriptions, and hostel costs.',
    color: '#3B82F6',
  },
  'student-budget': {
    id: 'student-budget',
    title: 'Budget Planner',
    icon: 'PieChart',
    description: 'Plan weekly expenditures, categorize food, entertainment, and utilities.',
    color: '#10B981',
  },
  'student-goals': {
    id: 'student-goals',
    title: 'Goal Milestones',
    icon: 'Target',
    description: 'Achievements, financial streak records, and reward tracking.',
    color: '#F59E0B',
  },

  // --- Working Professional Widgets ---
  'professional-salary': {
    id: 'professional-salary',
    title: 'Salary Management',
    icon: 'Briefcase',
    description: 'Detailed analysis of monthly base salary, bonuses, and side-hustles.',
    color: '#7C3AED',
  },
  'professional-expenses': {
    id: 'professional-expenses',
    title: 'Monthly Expenses',
    icon: 'TrendingDown',
    description: 'Categorized tracking of rent, bills, groceries, dining, and shopping.',
    color: '#EF4444',
  },
  'professional-assets': {
    id: 'professional-assets',
    title: 'Asset Overview',
    icon: 'Gem',
    description: 'Valuation summaries of real estate, gold, digital assets, and vehicles.',
    color: '#10B981',
  },
  'professional-networth': {
    id: 'professional-networth',
    title: 'Net Worth Tracker',
    icon: 'Coins',
    description: 'Live overview of net asset values subtracted by active liabilities.',
    color: '#F59E0B',
  },
  'professional-investments': {
    id: 'professional-investments',
    title: 'Investments Portfolio',
    icon: 'TrendingUp',
    description: 'Current yield and performance of stocks, mutual funds, SIPs, and PPF.',
    color: '#3B82F6',
  },

  // --- Business Widgets ---
  'business-revenue': {
    id: 'business-revenue',
    title: 'Business Revenue',
    icon: 'IndianRupee',
    description: 'Gross incoming sales revenue, invoice reports, and pipeline analytics.',
    color: '#4F46E5',
  },
  'business-profit': {
    id: 'business-profit',
    title: 'Net Profit Margin',
    icon: 'Sparkles',
    description: 'Net margins calculated after operational costs, taxes, and expenditures.',
    color: '#10B981',
  },
  'business-cashflow': {
    id: 'business-cashflow',
    title: 'Cash Flow Statements',
    icon: 'ArrowLeftRight',
    description: 'Real-time inflows and outflows tracking to ensure daily liquid capital.',
    color: '#0EA5E9',
  },
  'business-payroll': {
    id: 'business-payroll',
    title: 'Payroll & HR Costs',
    icon: 'Users',
    description: 'Track employee salaries, contractor retainers, and tax compliance.',
    color: '#EC4899',
  },
  'business-inventory': {
    id: 'business-inventory',
    title: 'Inventory & Stock',
    icon: 'Boxes',
    description: 'Stock valuation, turnover rate, product availability, and re-order limits.',
    color: '#F59E0B',
  },
};

/**
 * Register a new widget dynamically at runtime
 * @param {string} id - Unique widget ID
 * @param {object} metadata - Title, icon, description, color, component
 */
export const registerWidget = (id, metadata) => {
  if (widgetRegistry[id]) {
    console.warn(`Widget with ID "${id}" is already registered. Overwriting.`);
  }
  widgetRegistry[id] = { id, ...metadata };
};

/**
 * Resolve widget details from registry
 * @param {string} id - Widget ID
 * @returns {object|null} Resolved widget config
 */
export const getWidget = (id) => {
  return widgetRegistry[id] || null;
};

export default widgetRegistry;
