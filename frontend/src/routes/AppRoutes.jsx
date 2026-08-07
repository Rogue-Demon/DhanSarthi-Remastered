import React, { lazy } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import LazyLoader from './LazyLoader';
import ProtectedRoute from './ProtectedRoute';
import PublicRoute from './PublicRoute';

import { RootLayout, DashboardLayout, AuthLayout } from '@/layouts';
import NotFound from './NotFound';

// Lazy loading page components
const Dashboard = lazy(() => import('@/pages/Dashboard/Dashboard'));
const Profile = lazy(() => import('@/pages/Profile/Profile'));



const SettingsLayout = lazy(() => import('@/pages/Settings/SettingsLayout'));
const SettingsProfile = lazy(() => import('@/pages/Settings/ProfileSettings'));
const SettingsAppearance = lazy(() => import('@/pages/Settings/AppearanceSettings'));
const SettingsNotifications = lazy(() => import('@/pages/Settings/NotificationSettings'));
const SettingsPreferences = lazy(() => import('@/pages/Settings/PreferencesSettings'));
const SettingsPrivacy = lazy(() => import('@/pages/Settings/PrivacySettings'));
const SettingsSecurity = lazy(() => import('@/pages/Settings/SecuritySettings'));
const SettingsLanguage = lazy(() => import('@/pages/Settings/LanguageSettings'));
const SettingsAccessibility = lazy(() => import('@/pages/Settings/AccessibilitySettings'));
const SettingsDataExport = lazy(() => import('@/pages/Settings/DataExportSettings'));
const SettingsIntegrations = lazy(() => import('@/pages/Settings/IntegrationsSettings'));
const SettingsAbout = lazy(() => import('@/pages/Settings/AboutSettings'));
const Auth = lazy(() => import('@/pages/Auth/Auth'));
const Onboarding = lazy(() => import('@/pages/Onboarding/Onboarding'));
const SelectProfile = lazy(() => import('@/pages/Onboarding/SelectProfile'));

// Lazy loading nested Finance subpage components
const FinanceLayout = lazy(() => import('@/pages/Finance/FinanceLayout'));
const FinanceOverview = lazy(() => import('@/pages/Finance/Overview'));
const FinanceIncome = lazy(() => import('@/pages/Finance/Income'));
const FinanceExpenses = lazy(() => import('@/pages/Finance/Expenses'));
const FinanceAssets = lazy(() => import('@/pages/Finance/Assets'));
const FinanceLiabilities = lazy(() => import('@/pages/Finance/Liabilities'));
const FinanceBudget = lazy(() => import('@/pages/Finance/Budget'));
const FinanceCashFlow = lazy(() => import('@/pages/Finance/CashFlow'));
const FinanceGoals = lazy(() => import('@/pages/Finance/Goals'));

// Lazy loading nested Investments subpage components
const InvestmentLayout = lazy(() => import('@/pages/Investments/InvestmentLayout'));
const InvestmentPortfolio = lazy(() => import('@/pages/Investments/Portfolio'));
const InvestmentStocks = lazy(() => import('@/pages/Investments/Stocks'));
const InvestmentMutualFunds = lazy(() => import('@/pages/Investments/MutualFunds'));
const InvestmentSIP = lazy(() => import('@/pages/Investments/SIP'));
const InvestmentFixedDeposit = lazy(() => import('@/pages/Investments/FixedDeposit'));
const InvestmentRecurringDeposit = lazy(() => import('@/pages/Investments/RecurringDeposit'));
const InvestmentGold = lazy(() => import('@/pages/Investments/Gold'));
const InvestmentBonds = lazy(() => import('@/pages/Investments/Bonds'));
const InvestmentPPF = lazy(() => import('@/pages/Investments/PPF'));
const InvestmentNPS = lazy(() => import('@/pages/Investments/NPS'));

// Lazy loading nested AI Advisor subpage components
const AIAdvisorLayout = lazy(() => import('@/pages/AIAdvisor/AIAdvisorLayout'));
const AIChat = lazy(() => import('@/pages/AIAdvisor/Chat'));
const AIHistory = lazy(() => import('@/pages/AIAdvisor/History'));
const AISavedConversations = lazy(() => import('@/pages/AIAdvisor/SavedConversations'));
const AITemplates = lazy(() => import('@/pages/AIAdvisor/Templates'));
const AISettings = lazy(() => import('@/pages/AIAdvisor/Settings'));

// Lazy loading nested Reports subpage components
const ReportsLayout = lazy(() => import('@/pages/Reports/ReportsLayout'));
const ReportsOverview = lazy(() => import('@/pages/Reports/Overview'));
const ReportsDaily = lazy(() => import('@/pages/Reports/Daily'));
const ReportsWeekly = lazy(() => import('@/pages/Reports/Weekly'));
const ReportsMonthly = lazy(() => import('@/pages/Reports/Monthly'));
const ReportsAnnual = lazy(() => import('@/pages/Reports/Annual'));
const ReportsGoals = lazy(() => import('@/pages/Reports/Goals'));
const ReportsTrends = lazy(() => import('@/pages/Reports/Trends'));
const ReportsExport = lazy(() => import('@/pages/Reports/Export'));
const ReportsSettings = lazy(() => import('@/pages/Reports/Settings'));

export const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    errorElement: <NotFound />,
    children: [
      {
        path: '',
        element: <Navigate to="/dashboard" replace />,
      },
      {
        path: 'onboarding',
        element: <LazyLoader component={Onboarding} />,
      },
      {
        path: 'select-profile',
        element: <LazyLoader component={SelectProfile} />,
      },
      {
        path: '',
        element: (
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        ),
        children: [
          {
            path: 'dashboard',
            element: <LazyLoader component={Dashboard} />,
          },
          {
            path: 'profile',
            element: <LazyLoader component={Profile} />,
          },
          {
            path: 'finance',
            element: <LazyLoader component={FinanceLayout} />,
            children: [
              {
                path: '',
                element: <Navigate to="overview" replace />,
              },
              {
                path: 'overview',
                element: <LazyLoader component={FinanceOverview} />,
              },
              {
                path: 'income',
                element: <LazyLoader component={FinanceIncome} />,
              },
              {
                path: 'expenses',
                element: <LazyLoader component={FinanceExpenses} />,
              },
              {
                path: 'assets',
                element: <LazyLoader component={FinanceAssets} />,
              },
              {
                path: 'liabilities',
                element: <LazyLoader component={FinanceLiabilities} />,
              },
              {
                path: 'budget',
                element: <LazyLoader component={FinanceBudget} />,
              },
              {
                path: 'cash-flow',
                element: <LazyLoader component={FinanceCashFlow} />,
              },
              {
                path: 'goals',
                element: <LazyLoader component={FinanceGoals} />,
              },
            ],
          },
          {
            path: 'investments',
            element: <LazyLoader component={InvestmentLayout} />,
            children: [
              {
                path: '',
                element: <Navigate to="portfolio" replace />,
              },
              {
                path: 'portfolio',
                element: <LazyLoader component={InvestmentPortfolio} />,
              },
              {
                path: 'stocks',
                element: <LazyLoader component={InvestmentStocks} />,
              },
              {
                path: 'mutual-funds',
                element: <LazyLoader component={InvestmentMutualFunds} />,
              },
              {
                path: 'sip',
                element: <LazyLoader component={InvestmentSIP} />,
              },
              {
                path: 'fixed-deposit',
                element: <LazyLoader component={InvestmentFixedDeposit} />,
              },
              {
                path: 'recurring-deposit',
                element: <LazyLoader component={InvestmentRecurringDeposit} />,
              },
              {
                path: 'gold',
                element: <LazyLoader component={InvestmentGold} />,
              },
              {
                path: 'bonds',
                element: <LazyLoader component={InvestmentBonds} />,
              },
              {
                path: 'ppf',
                element: <LazyLoader component={InvestmentPPF} />,
              },
              {
                path: 'nps',
                element: <LazyLoader component={InvestmentNPS} />,
              },
            ],
          },
          {
            path: 'ai-advisor',
            element: <LazyLoader component={AIAdvisorLayout} />,
            children: [
              {
                path: '',
                element: <Navigate to="chat" replace />,
              },
              {
                path: 'chat',
                element: <LazyLoader component={AIChat} />,
              },
              {
                path: 'history',
                element: <LazyLoader component={AIHistory} />,
              },
              {
                path: 'saved',
                element: <LazyLoader component={AISavedConversations} />,
              },
              {
                path: 'templates',
                element: <LazyLoader component={AITemplates} />,
              },
              {
                path: 'settings',
                element: <LazyLoader component={AISettings} />,
              },
            ],
          },
          {
            path: 'reports',
            element: <LazyLoader component={ReportsLayout} />,
            children: [
              {
                path: '',
                element: <Navigate to="overview" replace />,
              },
              {
                path: 'overview',
                element: <LazyLoader component={ReportsOverview} />,
              },
              {
                path: 'daily',
                element: <LazyLoader component={ReportsDaily} />,
              },
              {
                path: 'weekly',
                element: <LazyLoader component={ReportsWeekly} />,
              },
              {
                path: 'monthly',
                element: <LazyLoader component={ReportsMonthly} />,
              },
              {
                path: 'annual',
                element: <LazyLoader component={ReportsAnnual} />,
              },
              {
                path: 'goals',
                element: <LazyLoader component={ReportsGoals} />,
              },
              {
                path: 'trends',
                element: <LazyLoader component={ReportsTrends} />,
              },
              {
                path: 'export',
                element: <LazyLoader component={ReportsExport} />,
              },
              {
                path: 'settings',
                element: <LazyLoader component={ReportsSettings} />,
              },
            ],
          },
          {
            path: 'settings',
            element: <LazyLoader component={SettingsLayout} />,
            children: [
              { path: '', element: <Navigate to='profile' replace /> },
              { path: 'profile', element: <LazyLoader component={SettingsProfile} /> },
              { path: 'appearance', element: <LazyLoader component={SettingsAppearance} /> },
              { path: 'notifications', element: <LazyLoader component={SettingsNotifications} /> },
              { path: 'preferences', element: <LazyLoader component={SettingsPreferences} /> },
              { path: 'privacy', element: <LazyLoader component={SettingsPrivacy} /> },
              { path: 'security', element: <LazyLoader component={SettingsSecurity} /> },
              { path: 'language', element: <LazyLoader component={SettingsLanguage} /> },
              { path: 'accessibility', element: <LazyLoader component={SettingsAccessibility} /> },
              { path: 'data-export', element: <LazyLoader component={SettingsDataExport} /> },
              { path: 'integrations', element: <LazyLoader component={SettingsIntegrations} /> },
              { path: 'about', element: <LazyLoader component={SettingsAbout} /> },
            ],
          },
        ],
      },
      {
        path: '',
        element: (
          <PublicRoute>
            <AuthLayout />
          </PublicRoute>
        ),
        children: [
          {
            path: 'auth',
            element: <LazyLoader component={Auth} />,
          },
        ],
      },
      {
        path: '*',
        element: <NotFound />,
      },
    ],
  },
]);

export default router;
