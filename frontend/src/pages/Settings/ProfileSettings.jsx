import React, { useState } from 'react';
import { useProfile } from '@/hooks';
import { motion, useReducedMotion } from 'framer-motion';
import { Button, Badge } from '@/components/ui';
import * as LucideIcons from 'lucide-react';

export function ProfileSettings() {
  const { profile, profileConfig } = useProfile();
  const shouldReduceMotion = useReducedMotion();

  const [name, setName] = useState('Shreyanshu');
  const [email, setEmail] = useState('shreyanshu@dhansarthi.app');
  const [occupation, setOccupation] = useState('Software Engineer');
  const [currency, setCurrency] = useState('INR (₹)');
  const [timezone, setTimezone] = useState('Asia/Kolkata (IST)');
  const [country, setCountry] = useState('India 🇮🇳');

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 w-full text-left select-none max-w-3xl mx-auto"
    >
      <div className="flex flex-col gap-1">
        <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">
          Personal Profile & Preferences
        </h3>
        <p className="text-xs font-bold text-text-muted">
          Manage your personal information, active financial persona, and geographic settings.
        </p>
      </div>

      <div className="clay-surface bg-card p-6 border border-white/60 dark:border-white/5 rounded-2xl shadow-card flex flex-col gap-6">
        
        {/* Avatar Row */}
        <div className="flex items-center gap-4 border-b border-border/60 pb-6">
          <div className="h-16 w-16 rounded-2xl bg-gradient-primary flex items-center justify-center text-white text-xl font-black shadow-floating shrink-0">
            S
          </div>
          <div className="flex flex-col gap-1 text-left">
            <div className="flex items-center gap-2">
              <span className="text-base font-black text-text-primary">{name}</span>
              <Badge variant="secondary" className="text-[8px] font-bold py-0.5 px-2 bg-primary/10 text-primary border-primary/20 rounded">
                {profile} Mode
              </Badge>
            </div>
            <span className="text-xs font-semibold text-text-muted">{email}</span>
          </div>
        </div>

        {/* Form Inputs */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-left">
          <div className="flex flex-col gap-1.5">
            <label className="text-[10px] font-black text-text-muted uppercase tracking-wider">Full Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3.5 py-2 text-xs font-bold rounded-xl border border-border bg-card text-text-primary focus:outline-none focus:border-primary"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-[10px] font-black text-text-muted uppercase tracking-wider">Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3.5 py-2 text-xs font-bold rounded-xl border border-border bg-card text-text-primary focus:outline-none focus:border-primary"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-[10px] font-black text-text-muted uppercase tracking-wider">Occupation</label>
            <input
              type="text"
              value={occupation}
              onChange={(e) => setOccupation(e.target.value)}
              className="w-full px-3.5 py-2 text-xs font-bold rounded-xl border border-border bg-card text-text-primary focus:outline-none focus:border-primary"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-[10px] font-black text-text-muted uppercase tracking-wider">Primary Currency</label>
            <input
              type="text"
              value={currency}
              disabled
              className="w-full px-3.5 py-2 text-xs font-bold rounded-xl border border-border bg-card/60 text-text-muted cursor-not-allowed"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-[10px] font-black text-text-muted uppercase tracking-wider">Timezone</label>
            <input
              type="text"
              value={timezone}
              disabled
              className="w-full px-3.5 py-2 text-xs font-bold rounded-xl border border-border bg-card/60 text-text-muted cursor-not-allowed"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-[10px] font-black text-text-muted uppercase tracking-wider">Country</label>
            <input
              type="text"
              value={country}
              disabled
              className="w-full px-3.5 py-2 text-xs font-bold rounded-xl border border-border bg-card/60 text-text-muted cursor-not-allowed"
            />
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t border-border/60">
          <Button variant="ghost" size="sm" onClick={() => alert('Profile reset')}>
            Reset
          </Button>
          <Button variant="gradient" size="sm" onClick={() => alert('Profile saved successfully')}>
            Save Changes
          </Button>
        </div>
      </div>
    </motion.div>
  );
}

export default ProfileSettings;
