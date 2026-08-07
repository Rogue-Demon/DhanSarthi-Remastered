import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import * as LucideIcons from 'lucide-react';

export function AboutSettings() {
  const shouldReduceMotion = useReducedMotion();

  const info = [
    { label: 'Version', value: '1.0.0-beta', icon: 'Tag' },
    { label: 'Build', value: '2024.06.15-r1', icon: 'Hammer' },
    { label: 'Platform', value: 'React 18 · Vite 5', icon: 'Layers' },
    { label: 'Design System', value: 'Claymorphism v2', icon: 'Palette' },
    { label: 'License', value: 'MIT License', icon: 'Scale' },
  ];

  const links = [
    { label: 'Documentation', icon: 'BookOpen', href: '#' },
    { label: 'Release Notes', icon: 'FileText', href: '#' },
    { label: 'GitHub Repository', icon: 'Github', href: '#' },
    { label: 'Report a Bug', icon: 'Bug', href: '#' },
    { label: 'Contact Support', icon: 'Mail', href: '#' },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 w-full text-left select-none max-w-3xl mx-auto"
    >
      <div className="flex flex-col gap-1">
        <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">About धनSarthi</h3>
        <p className="text-xs font-bold text-text-muted">Application details, version, and helpful links.</p>
      </div>

      {/* Logo & Tagline */}
      <div className="clay-surface bg-card p-6 border border-white/60 dark:border-white/5 rounded-2xl shadow-xs flex flex-col items-center gap-3">
        <div className="p-4 rounded-2xl bg-gradient-to-br from-primary to-primary-dark text-white shadow-lg">
          <LucideIcons.Landmark className="h-8 w-8" />
        </div>
        <h4 className="text-base font-black text-text-primary uppercase tracking-wider">धनSarthi</h4>
        <p className="text-[10px] font-bold text-text-muted text-center max-w-sm">
          Your AI-Powered Financial Companion — bridging the gap between financial literacy and actionable intelligence for Students, Professionals, and Businesses across India.
        </p>
      </div>

      {/* Info Grid */}
      <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl shadow-xs flex flex-col gap-3">
        <span className="text-[10px] font-black text-text-muted uppercase tracking-widest">Application Info</span>
        {info.map((item, i) => {
          const Icon = LucideIcons[item.icon] || LucideIcons.Info;
          return (
            <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-muted/20 border border-border/60">
              <div className="flex items-center gap-2">
                <Icon className="h-3.5 w-3.5 text-primary" />
                <span className="text-xs font-black text-text-muted">{item.label}</span>
              </div>
              <span className="text-xs font-black text-text-primary">{item.value}</span>
            </div>
          );
        })}
      </div>

      {/* Links */}
      <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl shadow-xs flex flex-col gap-3">
        <span className="text-[10px] font-black text-text-muted uppercase tracking-widest">Resources</span>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {links.map((link, i) => {
            const Icon = LucideIcons[link.icon] || LucideIcons.Link;
            return (
              <a key={i} href={link.href} className="flex items-center gap-2 p-3 rounded-xl bg-muted/20 border border-border/60 hover:border-primary/40 transition-colors cursor-pointer group">
                <Icon className="h-4 w-4 text-primary" />
                <span className="text-xs font-black text-text-muted group-hover:text-primary transition-colors">{link.label}</span>
                <LucideIcons.ExternalLink className="h-3 w-3 text-text-muted ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
              </a>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}

export default AboutSettings;
