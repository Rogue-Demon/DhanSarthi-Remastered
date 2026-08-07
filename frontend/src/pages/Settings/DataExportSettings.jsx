import React, { useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import * as LucideIcons from 'lucide-react';

export function DataExportSettings() {
  const shouldReduceMotion = useReducedMotion();
  const [exportFormat, setExportFormat] = useState('CSV');

  const exportOptions = [
    { label: 'Transactions', desc: 'All income & expense records', icon: 'ArrowUpDown', size: '~2.4 MB' },
    { label: 'Budget History', desc: 'Monthly budget plans & actuals', icon: 'PieChart', size: '~480 KB' },
    { label: 'Investment Portfolio', desc: 'Holdings, SIPs, returns data', icon: 'TrendingUp', size: '~1.1 MB' },
    { label: 'Reports Archive', desc: 'Generated analytics reports', icon: 'FileText', size: '~3.8 MB' },
    { label: 'AI Chat History', desc: 'Full advisor conversation logs', icon: 'MessageSquare', size: '~620 KB' },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 w-full text-left select-none max-w-3xl mx-auto"
    >
      <div className="flex flex-col gap-1">
        <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">Data & Export</h3>
        <p className="text-xs font-bold text-text-muted">Download your data or request a full account export.</p>
      </div>

      {/* Format Selector */}
      <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl shadow-xs flex flex-col gap-3">
        <span className="text-[10px] font-black text-text-muted uppercase tracking-widest">Export Format</span>
        <div className="flex gap-2">
          {['CSV', 'JSON', 'PDF'].map((fmt) => (
            <button
              key={fmt}
              onClick={() => setExportFormat(fmt)}
              className={`px-4 py-2 rounded-xl text-xs font-black uppercase tracking-wider border transition-all cursor-pointer ${
                exportFormat === fmt ? 'bg-primary text-white border-primary shadow-xs' : 'bg-card border-border text-text-muted hover:text-text-primary'
              }`}
            >
              {fmt}
            </button>
          ))}
        </div>
      </div>

      {/* Export Items */}
      <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl shadow-xs flex flex-col gap-3">
        <span className="text-[10px] font-black text-text-muted uppercase tracking-widest">Available Data</span>
        {exportOptions.map((opt, i) => {
          const Icon = LucideIcons[opt.icon] || LucideIcons.File;
          return (
            <div key={i} className="flex items-center justify-between p-4 rounded-xl bg-muted/20 border border-border/60">
              <div className="flex items-center gap-3">
                <Icon className="h-4 w-4 text-primary shrink-0" />
                <div className="flex flex-col gap-0.5">
                  <span className="text-xs font-black text-text-primary">{opt.label}</span>
                  <span className="text-[10px] font-bold text-text-muted">{opt.desc} · {opt.size}</span>
                </div>
              </div>
              <button className="px-3 py-1.5 text-[10px] font-black uppercase tracking-widest text-primary border border-primary/40 rounded-lg hover:bg-primary/10 transition-colors cursor-pointer flex items-center gap-1">
                <LucideIcons.Download className="h-3 w-3" /> Export
              </button>
            </div>
          );
        })}
      </div>

      {/* Danger Zone */}
      <div className="clay-surface bg-red-500/5 p-5 border border-red-400/30 rounded-2xl shadow-xs flex flex-col gap-3">
        <span className="text-[10px] font-black text-red-400 uppercase tracking-widest">Danger Zone</span>
        <div className="flex items-center justify-between p-4 rounded-xl bg-red-500/10 border border-red-400/30">
          <div className="flex flex-col gap-0.5">
            <span className="text-xs font-black text-red-400">Delete All Data</span>
            <span className="text-[10px] font-bold text-red-400/70">Permanently remove all personal data. This cannot be undone.</span>
          </div>
          <button className="px-4 py-2 text-[10px] font-black uppercase tracking-widest text-white bg-red-500 rounded-xl hover:bg-red-600 transition-colors cursor-pointer shadow-xs">Delete</button>
        </div>
      </div>
    </motion.div>
  );
}

export default DataExportSettings;
