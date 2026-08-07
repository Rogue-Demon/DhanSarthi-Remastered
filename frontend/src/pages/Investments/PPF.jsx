import React from 'react';
import { useProfile } from '@/hooks';
import { getInvestmentsConfig } from '@/config';
import { motion, useReducedMotion } from 'framer-motion';
import { DashboardGrid, WidgetContainer } from '@/components/dashboard';
import * as LucideIcons from 'lucide-react';
import { Badge } from '@/components/ui';

export function PPF() {
  const { profile } = useProfile();
  const shouldReduceMotion = useReducedMotion();
  const investData = getInvestmentsConfig(profile);

  const ppfs = investData?.ppf || [];

  if (ppfs.length === 0) {
    return (
      <div className="clay-surface bg-card border-2 border-white/60 rounded-3xl p-10 shadow-floating text-center flex flex-col items-center justify-center gap-4 select-none max-w-md mx-auto mt-10">
        <div className="h-14 w-14 rounded-2xl bg-muted border flex items-center justify-center text-text-muted">
          <LucideIcons.Landmark className="h-7 w-7" />
        </div>
        <div className="flex flex-col gap-1">
          <h4 className="text-sm font-black text-text-primary uppercase tracking-wider">No PPF Account Active</h4>
          <p className="text-xs font-bold text-text-muted max-w-[280px] leading-relaxed mt-1">
            Your profile focus doesn't include a Public Provident Fund. View other investment paths.
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
          Public Provident Fund (PPF)
        </h3>
        <p className="text-xs font-bold text-text-muted">
          Long-term tax-exempt government savings instrument with compound interest accrual.
        </p>
      </div>

      <DashboardGrid>
        {ppfs.map((ppf, idx) => {
          return (
            <motion.div
              key={ppf.summary}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.05 }}
              className="lg:col-span-12 md:col-span-2"
            >
              <div className="clay-surface bg-card p-6 border border-white/60 dark:border-white/5 shadow-card select-none relative group">
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-success transition-all duration-300 group-hover:w-1.5" />

                <div className="grid grid-cols-1 sm:grid-cols-4 gap-6 pl-2 text-left">
                  {/* Account Summary */}
                  <div className="flex flex-col gap-1">
                    <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">Account</span>
                    <span className="text-xs font-black text-text-primary">{ppf.summary}</span>
                  </div>

                  {/* Current Balance */}
                  <div className="flex flex-col gap-1">
                    <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">Current Balance</span>
                    <span className="text-xl font-black text-text-primary">{ppf.balance}</span>
                  </div>

                  {/* Annual Contribution */}
                  <div className="flex flex-col gap-1">
                    <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">Annual Contribution</span>
                    <span className="text-xs font-black text-text-primary">{ppf.contribution}</span>
                  </div>

                  {/* Interest & Maturity */}
                  <div className="flex flex-col gap-1">
                    <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">Interest Rate</span>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="text-[8px] font-bold py-0.5 px-1.5 bg-success/10 text-success border-success/15 rounded">
                        {ppf.interest} p.a.
                      </Badge>
                      <span className="text-[10px] font-bold text-text-muted">
                        Matures: {ppf.maturity}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          );
        })}
      </DashboardGrid>
    </motion.div>
  );
}

export default PPF;
