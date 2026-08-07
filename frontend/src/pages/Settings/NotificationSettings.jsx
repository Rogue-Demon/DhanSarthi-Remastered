import React, { useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import * as LucideIcons from 'lucide-react';

const ToggleRow = ({ label, desc, enabled, onToggle }) => (
  <div className="flex items-center justify-between p-4 rounded-xl bg-muted/20 border border-border/60">
    <div className="flex flex-col gap-0.5 text-left">
      <span className="text-xs font-black text-text-primary">{label}</span>
      <span className="text-[10px] font-bold text-text-muted">{desc}</span>
    </div>
    <button
      onClick={onToggle}
      className={`w-12 h-6 rounded-full transition-colors relative p-1 cursor-pointer shrink-0 ${
        enabled ? 'bg-primary' : 'bg-muted'
      }`}
    >
      <div className={`h-4 w-4 rounded-full bg-white transition-transform ${enabled ? 'translate-x-6' : 'translate-x-0'}`} />
    </button>
  </div>
);

export function NotificationSettings() {
  const shouldReduceMotion = useReducedMotion();
  const [notifs, setNotifs] = useState({
    budgetAlerts: true,
    goalReminders: true,
    investmentUpdates: false,
    expenseAlerts: true,
    reports: false,
    aiSuggestions: true,
    email: false,
    push: true,
    sms: false,
  });

  const toggle = (key) => setNotifs((prev) => ({ ...prev, [key]: !prev[key] }));

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 w-full text-left select-none max-w-3xl mx-auto"
    >
      <div className="flex flex-col gap-1">
        <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">Notification Preferences</h3>
        <p className="text-xs font-bold text-text-muted">Control which alerts, reminders, and update channels are active.</p>
      </div>

      <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl shadow-xs flex flex-col gap-3">
        <span className="text-[10px] font-black text-text-muted uppercase tracking-widest">Alert Types</span>
        <ToggleRow label="Budget Limit Alerts" desc="Notify when spending nears budget caps." enabled={notifs.budgetAlerts} onToggle={() => toggle('budgetAlerts')} />
        <ToggleRow label="Goal Milestone Reminders" desc="Progress updates on savings milestones." enabled={notifs.goalReminders} onToggle={() => toggle('goalReminders')} />
        <ToggleRow label="Investment Market Updates" desc="Portfolio NAV & market change summaries." enabled={notifs.investmentUpdates} onToggle={() => toggle('investmentUpdates')} />
        <ToggleRow label="Expense Category Alerts" desc="Unusual or high-value transaction flags." enabled={notifs.expenseAlerts} onToggle={() => toggle('expenseAlerts')} />
        <ToggleRow label="Report Generation Notices" desc="When weekly/monthly reports are ready." enabled={notifs.reports} onToggle={() => toggle('reports')} />
        <ToggleRow label="AI Advisory Suggestions" desc="Smart financial tips from DhanSarthi AI." enabled={notifs.aiSuggestions} onToggle={() => toggle('aiSuggestions')} />
      </div>

      <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl shadow-xs flex flex-col gap-3">
        <span className="text-[10px] font-black text-text-muted uppercase tracking-widest">Delivery Channels</span>
        <ToggleRow label="Email Notifications" desc="Receive alerts via registered email." enabled={notifs.email} onToggle={() => toggle('email')} />
        <ToggleRow label="Push Notifications" desc="In-browser and device push alerts." enabled={notifs.push} onToggle={() => toggle('push')} />
        <ToggleRow label="SMS Alerts" desc="Critical alerts delivered via SMS." enabled={notifs.sms} onToggle={() => toggle('sms')} />
      </div>
    </motion.div>
  );
}

export default NotificationSettings;
