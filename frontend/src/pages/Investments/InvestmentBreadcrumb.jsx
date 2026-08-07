import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import * as LucideIcons from 'lucide-react';

/**
 * InvestmentBreadcrumb Component
 * Renders page hierarchy paths for nested Investments subroutes.
 */
export function InvestmentBreadcrumb() {
  const location = useLocation();
  const pathnames = location.pathname.split('/').filter((x) => x);

  // Capitalize paths nicely
  const getLabel = (path) => {
    if (path === 'investments') return 'Investments';
    if (path === 'mutual-funds') return 'Mutual Funds';
    if (path === 'fixed-deposit') return 'Fixed Deposit';
    if (path === 'recurring-deposit') return 'Recurring Deposit';
    return path.toUpperCase();
  };

  return (
    <nav className="flex items-center gap-2 select-none text-xs font-bold text-text-muted">
      <Link to="/dashboard" className="hover:text-primary transition-colors flex items-center gap-1">
        <LucideIcons.Home className="h-3.5 w-3.5" />
        <span>Home</span>
      </Link>

      {pathnames.map((value, index) => {
        const to = `/${pathnames.slice(0, index + 1).join('/')}`;
        const isLast = index === pathnames.length - 1;

        return (
          <React.Fragment key={to}>
            <LucideIcons.ChevronRight className="h-3 w-3 shrink-0" />
            {isLast ? (
              <span className="text-text-secondary font-black">{getLabel(value)}</span>
            ) : (
              <Link to={to} className="hover:text-primary transition-colors">
                {getLabel(value)}
              </Link>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
}

export default InvestmentBreadcrumb;
