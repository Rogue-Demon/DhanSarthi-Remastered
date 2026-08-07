import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import * as LucideIcons from 'lucide-react';

const INTEGRATIONS = [
  { name: 'Google Pay', desc: 'Link UPI transactions for auto-categorisation.', icon: 'Wallet', status: 'connected', color: 'text-green-500' },
  { name: 'PhonePe', desc: 'Sync PhonePe spending and cashback data.', icon: 'Smartphone', status: 'available', color: 'text-text-muted' },
  { name: 'Zerodha / Kite', desc: 'Import live portfolio & trade history.', icon: 'TrendingUp', status: 'available', color: 'text-text-muted' },
  { name: 'Groww', desc: 'Mutual fund and stock data sync.', icon: 'BarChart3', status: 'connected', color: 'text-green-500' },
  { name: 'Google Sheets', desc: 'Export data to Google Sheets automatically.', icon: 'Sheet', status: 'available', color: 'text-text-muted' },
  { name: 'Telegram Bot', desc: 'Get alerts and summaries via Telegram.', icon: 'Send', status: 'available', color: 'text-text-muted' },
];

export function IntegrationsSettings() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 w-full text-left select-none max-w-3xl mx-auto"
    >
      <div className="flex flex-col gap-1">
        <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">Integrations</h3>
        <p className="text-xs font-bold text-text-muted">Connect third-party services to enrich your financial dashboard.</p>
      </div>

      <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl shadow-xs flex flex-col gap-3">
        {INTEGRATIONS.map((item, i) => {
          const Icon = LucideIcons[item.icon] || LucideIcons.Plug;
          const isConnected = item.status === 'connected';
          return (
            <div key={i} className="flex items-center justify-between p-4 rounded-xl bg-muted/20 border border-border/60">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-primary/10 text-primary shrink-0"><Icon className="h-4 w-4" /></div>
                <div className="flex flex-col gap-0.5">
                  <span className="text-xs font-black text-text-primary flex items-center gap-2">
                    {item.name}
                    {isConnected && <span className="px-1.5 py-0.5 text-[8px] font-black uppercase tracking-widest bg-green-500/15 text-green-500 rounded-md">Connected</span>}
                  </span>
                  <span className="text-[10px] font-bold text-text-muted">{item.desc}</span>
                </div>
              </div>
              <button className={`px-3 py-1.5 text-[10px] font-black uppercase tracking-widest rounded-lg transition-colors cursor-pointer ${
                isConnected
                  ? 'text-red-400 border border-red-400/40 hover:bg-red-400/10'
                  : 'text-primary border border-primary/40 hover:bg-primary/10'
              }`}>
                {isConnected ? 'Disconnect' : 'Connect'}
              </button>
            </div>
          );
        })}
      </div>
    </motion.div>
  );
}

export default IntegrationsSettings;
