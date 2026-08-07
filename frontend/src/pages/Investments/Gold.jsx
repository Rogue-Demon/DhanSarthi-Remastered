import React from 'react';
import { useProfile } from '@/hooks';
import { getInvestmentsConfig } from '@/config';
import { motion, useReducedMotion } from 'framer-motion';
import { DashboardGrid } from '@/components/dashboard';
import * as LucideIcons from 'lucide-react';
import { Badge } from '@/components/ui';

export function Gold() {
  const { profile } = useProfile();
  const shouldReduceMotion = useReducedMotion();
  const investData = getInvestmentsConfig(profile);

  const golds = investData?.gold || [];

  if (golds.length === 0) {
    return (
      <div className="clay-surface bg-card border-2 border-white/60 rounded-3xl p-10 shadow-floating text-center flex flex-col items-center justify-center gap-4 select-none max-w-md mx-auto mt-10">
        <div className="h-14 w-14 rounded-2xl bg-muted border flex items-center justify-center text-text-muted">
          <LucideIcons.Gem className="h-7 w-7" />
        </div>
        <div className="flex flex-col gap-1">
          <h4 className="text-sm font-black text-text-primary uppercase tracking-wider">No Gold Asset Holdings</h4>
          <p className="text-xs font-bold text-text-muted max-w-[280px] leading-relaxed mt-1">
            Your profile focus doesn't support active gold investments. View other investment paths.
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
          Precious Gold Bullions
        </h3>
        <p className="text-xs font-bold text-text-muted">
          Track digital and physical sovereign gold coins, gram quantities, and growth yields.
        </p>
      </div>

      <DashboardGrid>
        {golds.map((g, idx) => {
          return (
            <motion.div
              key={g.type}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.05 }}
              className="lg:col-span-6 md:col-span-1"
            >
              <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 shadow-card flex items-center justify-between gap-4 select-none relative group h-full">
                <div className="flex flex-col gap-1.5 text-left">
                  <span className="text-xs font-black text-text-primary group-hover:text-primary transition-colors duration-200">
                    {g.type}
                  </span>
                  <span className="text-lg font-black text-text-primary mt-1">
                    Value: {g.value}
                  </span>
                  
                  <div className="flex items-center gap-2 mt-2">
                    <Badge variant="secondary" className="text-[8px] font-bold py-0.5 px-1 bg-warning/10 text-warning border-warning/15 rounded">
                      Growth: {g.growth}
                    </Badge>
                    <span className="text-[10px] font-bold text-text-muted">
                      Qty: {g.qty}
                    </span>
                  </div>
                </div>

                <div className="p-3.5 rounded-2xl flex items-center justify-center border bg-warning/10 text-warning shadow-xs shrink-0">
                  <LucideIcons.Gem className="h-5 w-5 stroke-[2px]" />
                </div>
              </div>
            </motion.div>
          );
        })}
      </DashboardGrid>
    </motion.div>
  );
}

export default Gold;
