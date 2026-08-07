import React from 'react';
import { useProfile } from '@/hooks';
import { getInvestmentsConfig } from '@/config';
import { motion, useReducedMotion } from 'framer-motion';
import { DashboardGrid } from '@/components/dashboard';
import * as LucideIcons from 'lucide-react';
import { Badge } from '@/components/ui';

export function MutualFunds() {
  const { profile } = useProfile();
  const shouldReduceMotion = useReducedMotion();
  const investData = getInvestmentsConfig(profile);

  const mfs = investData?.mutualFunds || [];

  if (mfs.length === 0) {
    return (
      <div className="clay-surface bg-card border-2 border-white/60 rounded-3xl p-10 shadow-floating text-center flex flex-col items-center justify-center gap-4 select-none max-w-md mx-auto mt-10">
        <div className="h-14 w-14 rounded-2xl bg-muted border flex items-center justify-center text-text-muted">
          <LucideIcons.BarChart2 className="h-7 w-7" />
        </div>
        <div className="flex flex-col gap-1">
          <h4 className="text-sm font-black text-text-primary uppercase tracking-wider">No Mutual Funds Logged</h4>
          <p className="text-xs font-bold text-text-muted max-w-[280px] leading-relaxed mt-1">
            Your profile focus doesn't support active mutual funds. View other investment paths.
          </p>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 w-full text-left"
    >
      <div className="flex flex-col gap-2">
        <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">
          Mutual Fund Ledger
        </h3>
        <p className="text-xs font-bold text-text-muted">
          Manage mutual funds portfolios, NAV stats, and annualized return percentages.
        </p>
      </div>

      <DashboardGrid>
        {mfs.map((mf, idx) => {
          return (
            <motion.div
              key={mf.name}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.05 }}
              className="lg:col-span-6 md:col-span-1"
            >
              <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 shadow-card flex items-center justify-between gap-4 select-none relative group h-full">
                <div className="flex flex-col gap-1.5 text-left">
                  <span className="text-xs font-black text-text-primary group-hover:text-primary transition-colors duration-200">
                    {mf.name}
                  </span>
                  <span className="text-[10px] font-bold text-text-muted">
                    {mf.category}
                  </span>
                  
                  <div className="flex flex-wrap items-center gap-2 mt-2">
                    <span className="text-lg font-black text-text-primary">NAV: {mf.nav}</span>
                    <Badge variant="secondary" className="text-[8px] font-bold py-0.5 px-1.5 bg-success/10 text-success border-success/15 rounded">
                      Returns: {mf.returns}
                    </Badge>
                  </div>

                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="secondary" className="text-[8px] font-bold py-0.5 px-1 bg-primary/10 text-primary border-primary/15 rounded">
                      Risk: {mf.risk}
                    </Badge>
                    {mf.sipEnabled && (
                      <Badge variant="secondary" className="text-[8px] font-bold py-0.5 px-1 bg-accent/10 text-accent border-accent/15 rounded">
                        SIP Active
                      </Badge>
                    )}
                  </div>
                </div>

                <div className="p-3.5 rounded-2xl flex items-center justify-center border bg-primary/10 text-primary shadow-xs shrink-0">
                  <LucideIcons.BarChart2 className="h-5 w-5 stroke-[2px]" />
                </div>
              </div>
            </motion.div>
          );
        })}
      </DashboardGrid>
    </motion.div>
  );
}

export default MutualFunds;
