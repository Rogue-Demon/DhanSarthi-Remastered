import React, { useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import * as LucideIcons from 'lucide-react';

export function SecuritySettings() {
  const shouldReduceMotion = useReducedMotion();
  const [twoFA, setTwoFA] = useState(false);
  const [biometric, setBiometric] = useState(false);

  const sessions = [
    { device: 'Chrome — Windows 11', ip: '192.168.1.***', lastActive: '2 min ago', current: true },
    { device: 'Safari — iPhone 15', ip: '192.168.1.***', lastActive: '3 hours ago', current: false },
    { device: 'Firefox — Ubuntu', ip: '10.0.0.***', lastActive: '2 days ago', current: false },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 w-full text-left select-none max-w-3xl mx-auto"
    >
      <div className="flex flex-col gap-1">
        <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">Security & Access</h3>
        <p className="text-xs font-bold text-text-muted">Manage authentication methods and review active sessions.</p>
      </div>

      {/* Password */}
      <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl shadow-xs flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-primary/10 text-primary shrink-0"><LucideIcons.Lock className="h-5 w-5" /></div>
          <div className="flex flex-col gap-0.5">
            <span className="text-xs font-black text-text-primary">Password</span>
            <span className="text-[10px] font-bold text-text-muted">Last changed 45 days ago</span>
          </div>
        </div>
        <button className="px-4 py-2 bg-primary text-white text-[10px] font-black uppercase tracking-widest rounded-xl shadow-xs cursor-pointer hover:opacity-90 transition-opacity">Change</button>
      </div>

      {/* 2FA */}
      <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl shadow-xs flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-primary/10 text-primary shrink-0"><LucideIcons.ShieldCheck className="h-5 w-5" /></div>
          <div className="flex flex-col gap-0.5">
            <span className="text-xs font-black text-text-primary">Two-Factor Authentication</span>
            <span className="text-[10px] font-bold text-text-muted">{twoFA ? 'Enabled — Authenticator App' : 'Not enabled'}</span>
          </div>
        </div>
        <button onClick={() => setTwoFA(!twoFA)} className={`w-12 h-6 rounded-full transition-colors relative p-1 cursor-pointer shrink-0 ${twoFA ? 'bg-primary' : 'bg-muted'}`}>
          <div className={`h-4 w-4 rounded-full bg-white transition-transform ${twoFA ? 'translate-x-6' : 'translate-x-0'}`} />
        </button>
      </div>

      {/* Biometric */}
      <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl shadow-xs flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-primary/10 text-primary shrink-0"><LucideIcons.Fingerprint className="h-5 w-5" /></div>
          <div className="flex flex-col gap-0.5">
            <span className="text-xs font-black text-text-primary">Biometric Login</span>
            <span className="text-[10px] font-bold text-text-muted">Face ID / Touch ID if device supports.</span>
          </div>
        </div>
        <button onClick={() => setBiometric(!biometric)} className={`w-12 h-6 rounded-full transition-colors relative p-1 cursor-pointer shrink-0 ${biometric ? 'bg-primary' : 'bg-muted'}`}>
          <div className={`h-4 w-4 rounded-full bg-white transition-transform ${biometric ? 'translate-x-6' : 'translate-x-0'}`} />
        </button>
      </div>

      {/* Sessions */}
      <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl shadow-xs flex flex-col gap-3">
        <span className="text-[10px] font-black text-text-muted uppercase tracking-widest">Active Sessions</span>
        {sessions.map((s, i) => (
          <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-muted/20 border border-border/60">
            <div className="flex items-center gap-3">
              <LucideIcons.Monitor className="h-4 w-4 text-text-muted" />
              <div className="flex flex-col gap-0.5">
                <span className="text-xs font-black text-text-primary">{s.device} {s.current && <span className="text-primary ml-1">(This device)</span>}</span>
                <span className="text-[10px] font-bold text-text-muted">{s.ip} · {s.lastActive}</span>
              </div>
            </div>
            {!s.current && (
              <button className="px-3 py-1.5 text-[10px] font-black uppercase tracking-widest text-red-400 border border-red-400/40 rounded-lg hover:bg-red-400/10 transition-colors cursor-pointer">Revoke</button>
            )}
          </div>
        ))}
      </div>
    </motion.div>
  );
}

export default SecuritySettings;
