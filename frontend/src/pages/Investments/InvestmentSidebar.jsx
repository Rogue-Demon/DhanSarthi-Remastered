import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import * as LucideIcons from 'lucide-react';
import { cn } from '@/utils';
import { motion } from 'framer-motion';
import { useProfile } from '@/hooks';
import { getInvestmentsConfig } from '@/config';

/**
 * InvestmentSidebar Component
 * Secondary navigation bar for the Investments module.
 * Adapts visible tabs dynamically based on the selected user profile's focus configuration.
 */
export function InvestmentSidebar({ className }) {
  const location = useLocation();
  const { profile } = useProfile();
  const investmentData = getInvestmentsConfig(profile);

  // Default focus tabs list if no profile active
  const focusTabs = investmentData?.focusTabs || ['portfolio'];

  const allNavItems = {
    'portfolio': { label: 'Portfolio', path: '/investments/portfolio', icon: 'PieChart' },
    'stocks': { label: 'Stocks', path: '/investments/stocks', icon: 'TrendingUp' },
    'mutual-funds': { label: 'Mutual Funds', path: '/investments/mutual-funds', icon: 'BarChart2' },
    'sip': { label: 'SIP Manager', path: '/investments/sip', icon: 'CalendarRange' },
    'fixed-deposit': { label: 'Fixed Deposits (FD)', path: '/investments/fixed-deposit', icon: 'FileCheck' },
    'recurring-deposit': { label: 'Recurring (RD)', path: '/investments/recurring-deposit', icon: 'RefreshCw' },
    'gold': { label: 'Gold Bullion', path: '/investments/gold', icon: 'Gem' },
    'bonds': { label: 'Commercial Bonds', path: '/investments/bonds', icon: 'Scale' },
    'ppf': { label: 'PPF Savings', path: '/investments/ppf', icon: 'Landmark' },
    'nps': { label: 'NPS Pension', path: '/investments/nps', icon: 'Coins' },
  };

  // Helper to check active state
  const isActivePath = (path) => {
    if (path === '/investments/portfolio') {
      return location.pathname === '/investments' || location.pathname === '/investments/portfolio';
    }
    return location.pathname === path;
  };

  return (
    <aside
      className={cn(
        // Mobile horizontal strip, Desktop sidebar column
        'flex md:flex-col gap-2 p-2 bg-card border-b md:border-b-0 md:border-r border-border/80 w-full md:w-56 shrink-0 overflow-x-auto md:overflow-x-visible scrollbar-none sticky top-16 z-10 md:h-[calc(100vh-4rem)] md:py-6 md:px-3 text-left select-none',
        className
      )}
    >
      {focusTabs.map((tabId) => {
        const item = allNavItems[tabId];
        if (!item) return null;

        const IconComponent = LucideIcons[item.icon] || LucideIcons.Layers;
        const active = isActivePath(item.path);

        return (
          <NavLink
            key={item.path}
            to={item.path}
            className={cn(
              'relative flex items-center gap-3 px-4.5 py-3 rounded-xl text-xs font-black uppercase tracking-wider transition-all duration-200 outline-none shrink-0 group',
              active
                ? 'text-primary'
                : 'text-text-muted hover:text-text-secondary hover:bg-muted/40'
            )}
          >
            {/* Active background pill element using Framer Motion */}
            {active && (
              <motion.div
                layoutId="active-investment-tab"
                className="absolute inset-0 bg-primary/10 border-l-3 border-primary rounded-xl z-[-1]"
                transition={{ type: 'spring', stiffness: 380, damping: 30 }}
              />
            )}

            <IconComponent className={cn('h-4.5 w-4.5 stroke-[2.2] shrink-0', active ? 'text-primary' : 'text-text-muted group-hover:text-text-secondary')} />
            <span>{item.label}</span>
          </NavLink>
        );
      })}
    </aside>
  );
}

export default InvestmentSidebar;
