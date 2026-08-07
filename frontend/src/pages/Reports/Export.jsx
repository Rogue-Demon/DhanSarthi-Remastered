import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { Button, Badge } from '@/components/ui';
import * as LucideIcons from 'lucide-react';

export function Export() {
  const shouldReduceMotion = useReducedMotion();

  const exportFormats = [
    { format: 'PDF Document', desc: 'Formatted executive summary report with embedded charts', icon: 'FileText', color: '#EF4444' },
    { format: 'Excel Spreadsheet (.xlsx)', desc: 'Detailed raw ledger tables and calculation formulas', icon: 'Table', color: '#10B981' },
    { format: 'CSV Ledger (.csv)', desc: 'Standard data export compatible with all accounting tools', icon: 'FileCode', color: '#3B82F6' },
    { format: 'Print Report', desc: 'Optimized high-contrast layout for direct paper printing', icon: 'Printer', color: '#7C3AED' },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 w-full text-left select-none max-w-4xl mx-auto"
    >
      <div className="flex flex-col gap-1">
        <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">
          Export Center
        </h3>
        <p className="text-xs font-bold text-text-muted">
          Download, print, or share formatted financial statement reports.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {exportFormats.map((fmt, idx) => {
          const Icon = LucideIcons[fmt.icon] || LucideIcons.Download;

          return (
            <div
              key={fmt.format}
              className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl shadow-card flex flex-col justify-between gap-4 text-left group"
            >
              <div className="flex items-center gap-3">
                <div
                  className="p-2.5 rounded-xl flex items-center justify-center shrink-0 border shadow-xs"
                  style={{
                    background: `${fmt.color}12`,
                    color: fmt.color,
                    borderColor: `${fmt.color}25`,
                  }}
                >
                  <Icon className="h-5 w-5 stroke-[2.2]" />
                </div>
                <div className="flex flex-col gap-0.5">
                  <span className="text-xs font-black text-text-primary group-hover:text-primary transition-colors">
                    {fmt.format}
                  </span>
                  <span className="text-[10px] font-bold text-text-muted">
                    {fmt.desc}
                  </span>
                </div>
              </div>

              <Button
                variant="secondary"
                size="sm"
                className="w-full rounded-xl font-bold text-xs justify-center border-border hover:border-primary/30 text-text-primary bg-card"
                onClick={() => alert(`Exporting ${fmt.format} placeholder`)}
                iconLeft={<LucideIcons.Download className="h-3.5 w-3.5" />}
              >
                Export {fmt.format.split(' ')[0]}
              </Button>
            </div>
          );
        })}
      </div>
    </motion.div>
  );
}

export default Export;
