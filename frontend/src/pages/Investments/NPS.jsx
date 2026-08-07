import React from 'react';
import { useProfile } from '@/hooks';
import { getInvestmentsConfig } from '@/config';
import { motion, useReducedMotion } from 'framer-motion';
import { DashboardGrid, WidgetContainer } from '@/components/dashboard';
import * as LucideIcons from 'lucide-react';
import { Badge } from '@/components/ui';

export function NPS() {
  const { profile } = useProfile();
  const shouldReduceMotion = useReducedMotion();
  const investData = getInvestmentsConfig(profile);

  const nps = investData?.nps;

  if (!nps) {
    return (
      <div className="clay-surface bg-card border-2 border-white/60 rounded-3xl p-10 shadow-floating text-center flex flex-col items-center justify-center gap-4 select-none max-w-md mx-auto mt-10">
        <div className="h-14 w-14 rounded-2xl bg-muted border flex items-center justify-center text-text-muted">
          <LucideIcons.Coins className="h-7 w-7" />
        </div>
        <div className="flex flex-col gap-1">
          <h4 className="text-sm font-black text-text-primary uppercase tracking-wider">No NPS Account Active</h4>
          <p className="text-xs font-bold text-text-muted max-w-[280px] leading-relaxed mt-1">
            Your profile focus doesn't include National Pension System contributions. View other investment paths.
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
          National Pension System (NPS)
        </h3>
        <p className="text-xs font-bold text-text-muted">
          Government-backed retirement savings with equity, corporate debt, and government bond allocations.
        </p>
      </div>

      <DashboardGrid>
        {/* Full-width NPS Account Card */}
        <div className="lg:col-span-12 md:col-span-2">
          <div className="clay-surface bg-card p-6 border border-white/60 dark:border-white/5 shadow-card select-none relative group">
            <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary transition-all duration-300 group-hover:w-1.5" />

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 pl-2 text-left">
              {/* Current Corpus */}
              <div className="flex flex-col gap-1">
                <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">Current Corpus</span>
                <span className="text-2xl font-black text-text-primary tracking-tight">{nps.corpus}</span>
                <span className="text-[10px] font-bold text-text-muted mt-0.5">Monthly: {nps.contribution}</span>
              </div>

              {/* Tier & Fund Allocation */}
              <div className="flex flex-col gap-1">
                <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">Tier & Allocation</span>
                <Badge variant="secondary" className="mr-auto text-[9px] font-bold py-0.5 px-2 bg-primary/10 text-primary border-primary/15 rounded mt-1">
                  {nps.tier}
                </Badge>
                <span className="text-[10px] font-bold text-text-secondary mt-1.5 leading-relaxed">
                  {nps.allocation}
                </span>
              </div>

              {/* Retirement Projection */}
              <div className="flex flex-col gap-1">
                <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">Retirement Projection</span>
                <div className="flex items-start gap-2 mt-1">
                  <div className="h-5 w-5 rounded-full bg-success/10 flex items-center justify-center shrink-0 text-success mt-0.5">
                    <LucideIcons.Sparkles className="h-3 w-3" />
                  </div>
                  <p className="text-xs font-semibold text-text-secondary leading-relaxed">
                    {nps.projection}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* NPS Growth Chart Placeholder */}
        <WidgetContainer
          title="NPS Corpus Growth Projection"
          icon="TrendingUp"
          sizeClass="lg:col-span-12"
        >
          <div className="h-32 w-full rounded-2xl bg-card border border-border/80 relative flex items-end justify-between px-8 pb-3 overflow-hidden mt-2">
            <div className="absolute inset-0 opacity-[0.02] bg-[radial-gradient(#7C3AED_1px,transparent_1px)] [background-size:12px_12px]" />
            
            {/* Visual graph path */}
            <svg className="absolute inset-0 w-full h-full text-primary/10" preserveAspectRatio="none" viewBox="0 0 100 100">
              <path d="M0,95 Q15,90 30,80 T60,50 T90,20 T100,10 L100,100 Z" fill="currentColor" />
              <path d="M0,95 Q15,90 30,80 T60,50 T90,20 T100,10" fill="none" stroke="var(--primary)" strokeWidth="2" />
            </svg>

            {['2026', '2030', '2035', '2040', '2050'].map((yr) => (
              <span key={yr} className="text-[9px] font-black text-text-muted z-10">{yr}</span>
            ))}

            <div className="absolute top-3 right-4 flex items-center gap-1.5 text-[10px] font-bold text-text-muted">
              <LucideIcons.Sparkles className="h-3.5 w-3.5 text-accent animate-pulse" />
              <span>Projected growth trajectory</span>
            </div>
          </div>
        </WidgetContainer>
      </DashboardGrid>
    </motion.div>
  );
}

export default NPS;
