export const ENDPOINTS = {
  auth: {
    login: '/auth/login',
    register: '/auth/register',
    logout: '/auth/logout',
    me: '/auth/me',
  },
  profile: {
    get: '/profile',
    update: '/profile/update',
  },
  finance: {
    overview: '/finance/overview',
    transactions: '/finance/transactions',
    budgets: '/finance/budgets',
  },
  investments: {
    portfolio: '/investments/portfolio',
    holdings: '/investments/holdings',
  },
  advisor: {
    chat: '/advisor/chat',
    history: '/advisor/history',
  },
  reports: {
    get: '/reports/download',
  },
};

export default ENDPOINTS;
