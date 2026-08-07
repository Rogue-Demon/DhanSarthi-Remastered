import React from 'react';
import { useProfile } from '@/hooks';
import { getFinanceConfig } from '@/config';
import { motion, useReducedMotion } from 'framer-motion';
import { DashboardGrid, WidgetContainer } from '@/components/dashboard';
import * as LucideIcons from 'lucide-react';
import { Badge } from '@/components/ui';

export function Liabilities() {
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
          {financeData.liabilities.title}
        </h3>
        <p className="text-xs font-bold text-text-muted">
          Monitor active loan liabilities, credit cards, outstanding invoices, and interest rates.
        </p>
      </div>

      <DashboardGrid>
        {financeData.liabilities.items.map((item, idx) => {
          const Icon = LucideIcons[item.icon] || LucideIcons.Handshake;

          return (
            <motion.div
              key={item.name}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.05 }}
              className="lg:col-span-6 md:col-span-1"
            >
              <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 shadow-card flex items-center justify-between gap-4 select-none relative group h-full">
                {/* Visual bar */}
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-danger transition-all duration-300 group-hover:w-1.5" />

                <div className="flex flex-col gap-1.5 pl-2 text-left">
                  <span className="text-xs font-black text-text-primary group-hover:text-primary transition-colors duration-200">
                    {item.name}
                  </span>
                  <span className="text-2xl font-black text-text-primary tracking-tight leading-none mt-1">
                    {item.value}
                  </span>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="secondary" className="text-[8px] font-bold py-0.5 px-1 bg-danger/10 text-danger border-danger/15 rounded">
                      Rate: {item.rate || 'None'}
                    </Badge>
                    <span className="text-[10px] font-bold text-text-muted">
                      {item.due}
                    </span>
                  </div>
                </div>

                <div className="p-3.5 rounded-2xl flex items-center justify-center border border-white/40 dark:border-white/5 bg-danger/10 text-danger shadow-xs shrink-0">
                  <Icon className="h-5 w-5 stroke-[2px]" />
                </div>
              </div>
            </motion.div>
          );
        })}
      </DashboardGrid>
    </motion.div>
  );
}

export default Liabilities;
