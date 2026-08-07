import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import * as LucideIcons from 'lucide-react';
import { cn } from '@/utils';
import { motion } from 'framer-motion';

/**
 * FinanceSidebar Component
 * Secondary navigation bar for the Finance module.
 * Renders as a left sidebar on desktop and a horizontal scrollable tab-bar on mobile.
 */
export function FinanceSidebar({ className }) {
  const location = useLocation();

  const navItems = [
    { label: 'Overview', path: '/finance/overview', icon: 'LayoutDashboard' },
    { label: 'Income', path: '/finance/income', icon: 'ArrowUpRight' },
    { label: 'Expenses', path: '/finance/expenses', icon: 'ArrowDownLeft' },
    { label: 'Assets', path: '/finance/assets', icon: 'Gem' },
    { label: 'Liabilities', path: '/finance/liabilities', icon: 'Handshake' },
    { label: 'Budget', path: '/finance/budget', icon: 'PieChart' },
    { label: 'Cash Flow', path: '/finance/cash-flow', icon: 'RefreshCw' },
    { label: 'Goals', path: '/finance/goals', icon: 'Target' },
  ];

  // Helper to check active state
  const isActivePath = (path) => {
    if (path === '/finance/overview') {
      return location.pathname === '/finance' || location.pathname === '/finance/overview';
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
      {navItems.map((item) => {
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
                layoutId="active-finance-tab"
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

export default FinanceSidebar;
