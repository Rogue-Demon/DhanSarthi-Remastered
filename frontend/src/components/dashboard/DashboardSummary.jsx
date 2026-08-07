import React from 'react';
import { useProfile } from '@/hooks';
import { PROFILES } from '@/constants';
import * as LucideIcons from 'lucide-react';
import { cn } from '@/utils';

/**
 * DashboardSummary Component
 *
 * Renders a row of metric placeholder cards (summary strip) representing key
 * financial indicators customized for the active profile.
 */
export function DashboardSummary({ className, ...props }) {
  const { profile, profileConfig } = useProfile();

  if (!profileConfig) return null;

  // Resolved mock data structures depending on profile context
  const getSummaryMetrics = () => {
    switch (profile) {
      case PROFILES.STUDENT:
        return [
          { label: 'Monthly Allowance', value: '₹5,000', icon: 'Wallet', trend: '+10% stipend', color: '#8B5CF6' },
          { label: 'Savings Balance', value: '₹12,450', icon: 'PiggyBank', trend: '82% of goal reached', color: '#EC4899' },
          { label: 'Weekly Expenditures', value: '₹840', icon: 'TrendingDown', trend: '₹160 remaining', color: '#EF4444' },
          { label: 'Active Goal Streaks', value: '14 Days', icon: 'Flame', trend: 'Top saver award', color: '#F59E0B' },
        ];
      case PROFILES.PROFESSIONAL:
        return [
          { label: 'Net Monthly Salary', value: '₹95,000', icon: 'Briefcase', trend: 'Credited 1st Aug', color: '#7C3AED' },
          { label: 'Accumulated Assets', value: '₹8,45,000', icon: 'Gem', trend: 'Mutual funds & FD', color: '#10B981' },
          { label: 'Active Liabilities', value: '₹1,20,000', icon: 'Handshake', trend: 'Car loan amortization', color: '#EF4444' },
          { label: 'Current Net Worth', value: '₹7,25,000', icon: 'Coins', trend: '+4.2% this month', color: '#F59E0B' },
        ];
      case PROFILES.BUSINESS:
        return [
          { label: 'Gross Monthly Revenue', value: '₹4,85,000', icon: 'IndianRupee', trend: '+15.2% MoM profit', color: '#4F46E5' },
          { label: 'Estimated Profit Margin', value: '₹1,45,000', icon: 'Sparkles', trend: '30% operating margin', color: '#10B981' },
          { label: 'Operational Cost (OPEX)', value: '₹3,40,000', icon: 'TrendingDown', trend: 'Includes payroll & stock', color: '#EF4444' },
          { label: 'Liquidity Cash Flow', value: '₹2,10,000', icon: 'RefreshCw', trend: 'Excellent cash ratio', color: '#0EA5E9' },
        ];
      default:
        return [];
    }
  };

  const metrics = getSummaryMetrics();

  return (
    <div
      className={cn(
        'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 w-full',
        className
      )}
      {...props}
    >
      {metrics.map((metric, idx) => {
        const IconComponent = LucideIcons[metric.icon] || LucideIcons.Layers;

        return (
          <div
            key={idx}
            className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 shadow-card flex items-center justify-between gap-4 select-none relative group overflow-hidden"
          >
            {/* Soft decorative background highlight bar */}
            <div
              className="absolute left-0 top-0 bottom-0 w-1 transition-all duration-300 group-hover:w-1.5"
              style={{ background: metric.color }}
            />

            <div className="flex flex-col gap-1.5 text-left pl-1">
              <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                {metric.label}
              </span>
              <span className="text-2xl font-black text-text-primary tracking-tight leading-none">
                {metric.value}
              </span>
              <span className="text-[10px] font-bold text-text-secondary">
                {metric.trend}
              </span>
            </div>

            {/* Icon Container with clay-like depth */}
            <div
              className="p-3.5 rounded-2xl flex items-center justify-center border border-white/40 dark:border-white/5 shadow-xs shrink-0"
              style={{
                background: `${metric.color}10`,
                color: metric.color,
              }}
            >
              <IconComponent className="h-5 w-5 stroke-[2px]" />
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default DashboardSummary;
