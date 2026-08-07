import React, { useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import * as LucideIcons from 'lucide-react';

export function PrivacySettings() {
  const shouldReduceMotion = useReducedMotion();
  const [dataSharing, setDataSharing] = useState(false);
  const [analytics, setAnalytics] = useState(true);
  const [cookies, setCookies] = useState(true);

  const ToggleCard = ({ title, desc, icon, enabled, onToggle }) => {
    const Icon = LucideIcons[icon] || LucideIcons.Shield;
    return (
      <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl shadow-xs flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-primary/10 text-primary shrink-0"><Icon className="h-5 w-5" /></div>
          <div className="flex flex-col gap-0.5 text-left">
            <span className="text-xs font-black text-text-primary">{title}</span>
            <span className="text-[10px] font-bold text-text-muted">{desc}</span>
          </div>
        </div>
        <button onClick={onToggle} className={`w-12 h-6 rounded-full transition-colors relative p-1 cursor-pointer shrink-0 ${enabled ? 'bg-primary' : 'bg-muted'}`}>
          <div className={`h-4 w-4 rounded-full bg-white transition-transform ${enabled ? 'translate-x-6' : 'translate-x-0'}`} />
        </button>
      </div>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 w-full text-left select-none max-w-3xl mx-auto"
    >
      <div className="flex flex-col gap-1">
        <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">Privacy & Data Controls</h3>
        <p className="text-xs font-bold text-text-muted">Manage data sharing, analytics collection, and cookie policies.</p>
      </div>

      <ToggleCard title="Anonymous Data Sharing" desc="Share anonymised usage patterns to improve DhanSarthi." icon="Share2" enabled={dataSharing} onToggle={() => setDataSharing(!dataSharing)} />
      <ToggleCard title="Application Analytics" desc="Allow internal usage analytics for performance monitoring." icon="BarChart" enabled={analytics} onToggle={() => setAnalytics(!analytics)} />
      <ToggleCard title="Cookie Consent" desc="Enable functional and analytics browser cookies." icon="Cookie" enabled={cookies} onToggle={() => setCookies(!cookies)} />
    </motion.div>
  );
}

export default PrivacySettings;
