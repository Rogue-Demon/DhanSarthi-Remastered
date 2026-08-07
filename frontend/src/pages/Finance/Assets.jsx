import React from 'react';
import { useProfile } from '@/hooks';
import { getFinanceConfig } from '@/config';
import { motion, useReducedMotion } from 'framer-motion';
import { DashboardGrid, WidgetContainer } from '@/components/dashboard';
import * as LucideIcons from 'lucide-react';
import { Badge } from '@/components/ui';

export function Assets() {
  const { profile } = useProfile();
  const shouldReduceMotion = useReducedMotion();
  const financeData = getFinanceConfig(profile);

  if (!financeData) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 w-full text-left"
    >
      <div className="flex flex-col gap-2">
        <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">
          {financeData.assets.title}
        </h3>
        <p className="text-xs font-bold text-text-muted">
          Track property values, checking/savings cash balance, and investment equity.
        </p>
      </div>

      <DashboardGrid>
        {financeData.assets.items.map((item, idx) => {
          const Icon = LucideIcons[item.icon] || LucideIcons.Gem;

          return (
            <motion.div
              key={item.name}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.05 }}
              className="lg:col-span-4 md:col-span-1"
            >
              <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 shadow-card flex items-center justify-between gap-4 select-none relative group h-full">
                {/* Visual bar */}
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-success transition-all duration-300 group-hover:w-1.5" />

                <div className="flex flex-col gap-1.5 pl-2 text-left">
                  <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                    {item.name}
                  </span>
                  <span className="text-2xl font-black text-text-primary tracking-tight leading-none">
                    {item.value}
                  </span>
                  <span className="text-[10px] font-bold text-text-secondary">
                    {item.type}
                  </span>
                </div>

                <div className="p-3.5 rounded-2xl flex items-center justify-center border border-white/40 dark:border-white/5 bg-success/10 text-success shadow-xs shrink-0">
                  <Icon className="h-5 w-5 stroke-[2px]" />
                </div>
              </div>
            </motion.div>
          );
        })}

        {/* Premium Asset Allocation Chart Placeholder */}
        <WidgetContainer
          title="Asset Allocation Valuations"
          icon="TrendingUp"
          sizeClass="lg:col-span-12"
        >
          <div className="h-28 w-full rounded-2xl bg-card border border-border/80 relative flex items-end justify-around px-8 pb-3 overflow-hidden mt-2">
            <div className="absolute inset-0 opacity-[0.02] bg-[radial-gradient(#7C3AED_1px,transparent_1px)] [background-size:10px_10px]" />
            
            {/* Visual graph path */}
            <div className="absolute top-2 left-4 flex gap-2">
              <span className="text-[9px] font-black text-text-muted uppercase">Liquidity and assets split</span>
            </div>

            {/* Horizontal bars mapping */}
            <div className="flex items-center gap-3 w-full px-2">
              <div className="h-4 rounded-full bg-success flex-grow" style={{ width: '55%' }} />
              <div className="h-4 rounded-full bg-primary flex-grow" style={{ width: '30%' }} />
              <div className="h-4 rounded-full bg-accent flex-grow" style={{ width: '15%' }} />
            </div>
          </div>
        </WidgetContainer>
      </DashboardGrid>
    </motion.div>
  );
}

export default Assets;
