import React from 'react';
import { useProfile } from '@/hooks';
import { getFinanceConfig } from '@/config';
import { motion, useReducedMotion } from 'framer-motion';
import { DashboardGrid, WidgetContainer } from '@/components/dashboard';
import * as LucideIcons from 'lucide-react';
import { Badge, Button } from '@/components/ui';

export function Goals() {
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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex flex-col gap-2">
          <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">
            Long-term Savings Goals
          </h3>
          <p className="text-xs font-bold text-text-muted">
            Configure, manage, and track progress targets for savings and investments.
          </p>
        </div>
        <Button
          variant="gradient"
          size="sm"
          onClick={() => alert('New Goal Creation Wizard placeholder')}
          className="rounded-xl font-bold text-xs gap-1.5 shadow-button"
          iconLeft={<LucideIcons.Plus className="h-4 w-4" />}
        >
          Create Goal Target
        </Button>
      </div>

      <DashboardGrid>
        {financeData.goals.map((goal, idx) => {
          const GoalIcon = LucideIcons[goal.icon] || LucideIcons.Compass;
          const pct = Math.round((goal.current / goal.target) * 100);
          const remaining = goal.target - goal.current;

          return (
            <motion.div
              key={goal.name}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.05 }}
              className="lg:col-span-6 md:col-span-1"
            >
              <div className="clay-surface bg-card border border-white/60 dark:border-white/5 p-5 flex gap-4 shadow-card hover:border-primary/20 transition-all duration-200 h-full">
                {/* SVG Progress Circle */}
                <div className="relative h-16 w-16 flex items-center justify-center shrink-0">
                  <svg className="h-full w-full transform -rotate-90" viewBox="0 0 36 36">
                    <path
                      className="text-muted"
                      strokeWidth="3.5"
                      stroke="currentColor"
                      fill="transparent"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                    <path
                      className="transition-all duration-500"
                      strokeWidth="3.5"
                      strokeDasharray={`${pct}, 100`}
                      strokeLinecap="round"
                      stroke={goal.color}
                      fill="transparent"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center text-white shrink-0 p-3 rounded-full">
                    <div
                      className="h-8 w-8 rounded-full flex items-center justify-center text-white shadow-xs border"
                      style={{ background: goal.color }}
                    >
                      <GoalIcon className="h-4 w-4" />
                    </div>
                  </div>
                </div>

                {/* Info Text */}
                <div className="flex-1 flex flex-col justify-between text-left gap-1">
                  <div className="flex justify-between items-center text-xs font-black text-text-primary leading-none">
                    <span>{goal.name}</span>
                    <span className="text-[10px] font-bold text-text-muted">Target: {goal.due}</span>
                  </div>

                  <div className="flex justify-between items-center text-[10px] font-bold text-text-secondary mt-2">
                    <span>₹{goal.current.toLocaleString()} / ₹{goal.target.toLocaleString()}</span>
                    <span className="font-black text-text-primary">{pct}%</span>
                  </div>

                  <div className="w-full bg-muted h-1.5 rounded-full overflow-hidden border mt-1">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{ width: `${pct}%`, backgroundColor: goal.color }}
                    />
                  </div>

                  <div className="flex justify-between items-center text-[9px] font-bold text-text-muted uppercase tracking-wider mt-1.5 border-t border-border/40 pt-1.5">
                    <span>Remaining: ₹{remaining.toLocaleString()}</span>
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

export default Goals;
