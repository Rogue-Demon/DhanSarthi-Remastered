import React, { useState } from 'react';
import { useTheme } from '@/hooks';
import { THEMES } from '@/constants';
import { motion, useReducedMotion } from 'framer-motion';
import { Button, Badge } from '@/components/ui';
import * as LucideIcons from 'lucide-react';

export function AppearanceSettings() {
  const { theme, setTheme } = useTheme();
  const shouldReduceMotion = useReducedMotion();

  const [accent, setAccent] = useState('#7C3AED');
  const [fontSize, setFontSize] = useState('Medium');
  const [density, setDensity] = useState('Comfortable');
  const [animations, setAnimations] = useState(true);

  const accents = [
    { name: 'Purple (Default)', hex: '#7C3AED' },
    { name: 'Pink Accent', hex: '#EC4899' },
    { name: 'Emerald Success', hex: '#10B981' },
    { name: 'Blue Horizon', hex: '#3B82F6' },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 w-full text-left select-none max-w-3xl mx-auto"
    >
      <div className="flex flex-col gap-1">
        <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">
          Appearance & Themes
        </h3>
        <p className="text-xs font-bold text-text-muted">
          Customize the visual presentation, color themes, font density, and Framer Motion animations.
        </p>
      </div>

      <div className="flex flex-col gap-6">
        
        {/* Theme Selector */}
        <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl flex flex-col gap-3 shadow-xs">
          <span className="text-xs font-black text-text-primary uppercase tracking-wider">Color Theme</span>
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: 'Light', value: THEMES.LIGHT, icon: 'Sun' },
              { label: 'Dark', value: THEMES.DARK, icon: 'Moon' },
              { label: 'System', value: THEMES.SYSTEM, icon: 'Laptop' },
            ].map((t) => {
              const Icon = LucideIcons[t.icon];
              const active = theme === t.value;

              return (
                <button
                  key={t.value}
                  onClick={() => setTheme(t.value)}
                  className={`flex flex-col items-center gap-2 p-3.5 rounded-xl border text-xs font-bold transition-all cursor-pointer ${
                    active
                      ? 'bg-primary/10 border-primary text-primary font-black shadow-xs'
                      : 'bg-card border-border text-text-muted hover:text-text-primary'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  <span>{t.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Accent Color Selection */}
        <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl flex flex-col gap-3 shadow-xs">
          <span className="text-xs font-black text-text-primary uppercase tracking-wider">Primary Accent Color</span>
          <div className="flex flex-wrap items-center gap-3">
            {accents.map((acc) => (
              <button
                key={acc.hex}
                onClick={() => setAccent(acc.hex)}
                className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-xs font-bold cursor-pointer transition-all ${
                  accent === acc.hex ? 'border-primary bg-primary/10 text-primary' : 'border-border text-text-muted'
                }`}
              >
                <div className="h-4 w-4 rounded-full" style={{ backgroundColor: acc.hex }} />
                <span>{acc.name}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Animation Toggle */}
        <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl flex items-center justify-between shadow-xs">
          <div className="flex flex-col gap-0.5">
            <span className="text-xs font-black text-text-primary uppercase tracking-wider">Interface Motion</span>
            <span className="text-[10px] font-bold text-text-muted">Enable micro-animations and smooth page transitions.</span>
          </div>
          <button
            onClick={() => setAnimations(!animations)}
            className={`w-12 h-6 rounded-full transition-colors relative p-1 cursor-pointer ${
              animations ? 'bg-primary' : 'bg-muted'
            }`}
          >
            <div className={`h-4 w-4 rounded-full bg-white transition-transform ${animations ? 'translate-x-6' : 'translate-x-0'}`} />
          </button>
        </div>

      </div>
    </motion.div>
  );
}

export default AppearanceSettings;
