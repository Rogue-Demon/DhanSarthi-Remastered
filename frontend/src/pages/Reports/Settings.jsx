import React, { useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { Button } from '@/components/ui';

export function Settings() {
  const shouldReduceMotion = useReducedMotion();
  const [dateRange, setDateRange] = useState('Monthly');
  const [chartStyle, setChartStyle] = useState('Area');
  const [frequency, setFrequency] = useState('Monthly');

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 w-full text-left select-none max-w-3xl mx-auto"
    >
      <div className="flex flex-col gap-1">
        <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">
          Report Settings & Preferences
        </h3>
        <p className="text-xs font-bold text-text-muted">
          Configure default date windows, preferred Recharts display styles, and automated report schedules.
        </p>
      </div>

      <div className="flex flex-col gap-6">
        {/* Default Date Window */}
        <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl flex flex-col gap-3 shadow-xs">
          <div className="flex flex-col gap-1">
            <span className="text-xs font-black text-text-primary uppercase tracking-wider">Default Range</span>
            <span className="text-[10px] font-bold text-text-muted">Default time window when opening report dashboards.</span>
          </div>
          <div className="grid grid-cols-3 gap-2 pt-1">
            {['Weekly', 'Monthly', 'Annual'].map((r) => (
              <button
                key={r}
                onClick={() => setDateRange(r)}
                className={`py-2 px-3 rounded-xl text-xs font-black uppercase tracking-wider transition-all cursor-pointer border ${
                  dateRange === r
                    ? 'bg-primary text-white border-primary shadow-xs'
                    : 'bg-card border-border text-text-muted hover:text-text-primary'
                }`}
              >
                {r}
              </button>
            ))}
          </div>
        </div>

        {/* Preferred Chart Style */}
        <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl flex flex-col gap-3 shadow-xs">
          <div className="flex flex-col gap-1">
            <span className="text-xs font-black text-text-primary uppercase tracking-wider">Preferred Chart Visuals</span>
            <span className="text-[10px] font-bold text-text-muted">Primary visualization layout type.</span>
          </div>
          <div className="grid grid-cols-3 gap-2 pt-1">
            {['Area', 'Line', 'Bar'].map((c) => (
              <button
                key={c}
                onClick={() => setChartStyle(c)}
                className={`py-2 px-3 rounded-xl text-xs font-black uppercase tracking-wider transition-all cursor-pointer border ${
                  chartStyle === c
                    ? 'bg-primary text-white border-primary shadow-xs'
                    : 'bg-card border-border text-text-muted hover:text-text-primary'
                }`}
              >
                {c}
              </button>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export default Settings;
