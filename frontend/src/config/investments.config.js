import { PROFILES } from '@/constants';

/**
 * Reusable Investments Module Configuration
 *
 * Centralizes profile-specific investments focus navigation, allocation, risk metrics,
 * holding summaries, and lists for Student, Professional, and Business profiles.
 */
export const investmentsConfig = {
  [PROFILES.STUDENT]: {
    focusTabs: ['portfolio', 'sip', 'gold', 'ppf'], // Active navigation tabs from config
    summary: {
      totalValue: '₹16,950',
      todayChange: '+₹150',
      overallReturn: '+₹1,250 (+7.8%)',
      monthlyGrowth: '₹450/mo',
      riskLevel: 'Moderate',
      diversification: 'High',
    },
    riskScore: 48, // Moderate
    mutualFunds: [
      { name: 'Index Growth Direct Fund', category: 'Equity - Index', nav: '₹124.5', returns: '+12.4% p.a.', risk: 'High', sipEnabled: true },
    ],
    sip: [
      { name: 'Micro Nifty SIP', amount: '₹200/mo', nextDate: '10th Aug', expectedVal: '₹14,500', progress: '32%', reminder: 'Auto-Debit On' },
    ],
    gold: [
      { type: 'Digital Sovereign Gold', qty: '1.5 Grams', value: '₹10,500', date: '05th Jul 2026', growth: '+4.5%' },
    ],
    ppf: [
      { summary: 'State Bank PPF Account', balance: '₹6,450', contribution: '₹500/yr', interest: '7.1%', maturity: '2041' },
    ],
    holdings: [
      { name: 'Digital Gold (SGB)', allocation: '62%', value: '₹10,500', type: 'Commodity' },
      { name: 'Nifty Index Mutual Fund', allocation: '38%', value: '₹6,450', type: 'Equity' },
    ],
    insights: [
      { text: 'Your portfolio is well diversified with gold and index funds.', type: 'positive' },
      { text: 'SIP contributions are consistent and auto-debited on time.', type: 'positive' },
    ],
  },
  [PROFILES.PROFESSIONAL]: {
    focusTabs: ['portfolio', 'stocks', 'mutual-funds', 'sip', 'fixed-deposit', 'recurring-deposit', 'ppf', 'nps'],
    summary: {
      totalValue: '₹3,12,000',
      todayChange: '+₹4,200',
      overallReturn: '+₹38,500 (+14.1%)',
      monthlyGrowth: '₹15,000/mo',
      riskLevel: 'Moderately High',
      diversification: 'Optimal',
    },
    riskScore: 72, // Moderately High
    stocks: [
      { company: 'Reliance Industries', sector: 'Energy/Telecom', price: '₹2,950', change: '+1.2%', trend: 'up', watchlist: false },
      { company: 'HDFC Bank Ltd', sector: 'Financial Services', price: '₹1,640', change: '-0.8%', trend: 'down', watchlist: true },
      { company: 'Infosys Tech', sector: 'IT Services', price: '₹1,580', change: '+2.4%', trend: 'up', watchlist: false },
    ],
    mutualFunds: [
      { name: 'HDFC Mid-Cap Opportunities', category: 'Equity - Mid Cap', nav: '₹145.60', returns: '+18.4% p.a.', risk: 'High', sipEnabled: true },
      { name: 'ICICI Prudential Bluechip', category: 'Equity - Large Cap', nav: '₹84.20', returns: '+14.2% p.a.', risk: 'Moderate', sipEnabled: true },
    ],
    sip: [
      { name: 'HDFC Mid-Cap SIP', amount: '₹10,000/mo', nextDate: '05th Aug', expectedVal: '₹1,40,400', progress: '45%', reminder: 'Auto-Debit On' },
      { name: 'ICICI Bluechip SIP', amount: '₹5,000/mo', nextDate: '05th Aug', expectedVal: '₹1,09,200', progress: '35%', reminder: 'Auto-Debit On' },
    ],
    fixedDeposit: [
      { bank: 'HDFC Bank FD', principal: '₹20,000', rate: '7.1%', maturity: '12th Aug 2027', expectedVal: '₹21,420', status: 'Active' },
    ],
    recurringDeposit: [
      { bank: 'ICICI Bank RD', deposit: '₹5,000/mo', tenure: '12 Months', expectedVal: '₹62,450', progress: '50%' },
    ],
    ppf: [
      { summary: 'ICICI Bank PPF Account', balance: '₹31,200', contribution: '₹12,000/yr', interest: '7.1%', maturity: '2035' },
    ],
    nps: {
      corpus: '₹54,600',
      contribution: '₹5,000/mo',
      tier: 'Tier 1 - Active Choice',
      allocation: 'Equity 75%, Corporate Debt 15%, Gov Bonds 10%',
      projection: 'Estimated ₹1.2 Cr at retirement (age 60)',
    },
    holdings: [
      { name: 'Mutual Funds Portfolio', allocation: '45%', value: '₹1,40,400', type: 'Mutual Fund' },
      { name: 'Direct Equity Stocks', allocation: '35%', value: '₹1,09,200', type: 'Equity' },
      { name: 'PPF & NPS Accounts', allocation: '20%', value: '₹62,400', type: 'Retirement' },
    ],
    insights: [
      { text: 'Your portfolio has a high equity allocation. Consider shifting 10% to debt.', type: 'warning' },
      { text: 'Emergency fund coverage is at 5 months of opex. Goal nearly complete.', type: 'positive' },
    ],
  },
  [PROFILES.BUSINESS]: {
    focusTabs: ['portfolio', 'bonds', 'gold'], // Focus: Corporate reserve portfolios, liquid gold, commercial bonds
    summary: {
      totalValue: '₹6,45,000',
      todayChange: '+₹8,500',
      overallReturn: '+₹72,400 (+12.6%)',
      monthlyGrowth: '₹45,000/mo',
      riskLevel: 'Low',
      diversification: 'Conservative',
    },
    riskScore: 28, // Low
    bonds: [
      { name: 'NHAI tax-free Bonds', issuer: 'Gov of India', coupon: '7.8% p.a.', maturity: '2031', value: '₹2,50,000', risk: 'Low' },
      { name: 'PFC Commercial Debenture', issuer: 'Power Finance Corp', coupon: '8.4% p.a.', maturity: '2029', value: '₹1,50,000', risk: 'Low' },
    ],
    gold: [
      { type: 'Commercial Gold Bullion', qty: '35 Grams', value: '₹2,45,000', date: '01st Jun 2026', growth: '+6.2%' },
    ],
    holdings: [
      { name: 'Commercial Bonds ledger', allocation: '62%', value: '₹4,000', type: 'Debt' },
      { name: 'Physical Gold Bullions', allocation: '38%', value: '₹2,45,000', type: 'Commodity' },
    ],
    insights: [
      { text: 'Portfolio risk is low. Cash flows are backed by government AAA debt paper.', type: 'positive' },
      { text: 'Current commercial bonds offer interest tax-exemption.', type: 'info' },
    ],
  },
};

/**
 * Resolve investments configuration for a profile
 * @param {string} profileName - Selected user profile name
 * @returns {object|null} Config details
 */
export const getInvestmentsConfig = (profileName) => {
  return investmentsConfig[profileName] || null;
};

export default investmentsConfig;
