import React, { useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import * as LucideIcons from 'lucide-react';

export function AccessibilitySettings() {
  const shouldReduceMotion = useReducedMotion();
  const [reduceMotion, setReduceMotion] = useState(false);
  const [highContrast, setHighContrast] = useState(false);
  const [fontSize, setFontSize] = useState('Default');
  const [screenReader, setScreenReader] = useState(false);

  const ToggleRow = ({ icon, label, desc, enabled, onToggle }) => {
    const Icon = LucideIcons[icon] || LucideIcons.Eye;
    return (
      <div className="flex items-center justify-between p-4 rounded-xl bg-muted/20 border border-border/60">
        <div className="flex items-center gap-3">
          <Icon className="h-4 w-4 text-primary shrink-0" />
          <div className="flex flex-col gap-0.5 text-left">
            <span className="text-xs font-black text-text-primary">{label}</span>
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
        <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">Accessibility</h3>
        <p className="text-xs font-bold text-text-muted">Customise display and interaction settings for better usability.</p>
      </div>

      <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl shadow-xs flex flex-col gap-3">
        <ToggleRow icon="Zap" label="Reduce Motion" desc="Minimise UI animations and transitions." enabled={reduceMotion} onToggle={() => setReduceMotion(!reduceMotion)} />
        <ToggleRow icon="Contrast" label="High Contrast Mode" desc="Increase colour contrast for text and icons." enabled={highContrast} onToggle={() => setHighContrast(!highContrast)} />
        <ToggleRow icon="Monitor" label="Screen Reader Support" desc="Enhanced ARIA labelling and live regions." enabled={screenReader} onToggle={() => setScreenReader(!screenReader)} />
      </div>

      <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl shadow-xs flex flex-col gap-3">
        <span className="text-[10px] font-black text-text-muted uppercase tracking-widest">Font Size</span>
        <div className="flex flex-wrap gap-2">
          {['Small', 'Default', 'Large', 'Extra Large'].map((opt) => (
            <button
              key={opt}
              onClick={() => setFontSize(opt)}
              className={`px-4 py-2 rounded-xl text-xs font-black uppercase tracking-wider border transition-all cursor-pointer ${
                fontSize === opt ? 'bg-primary text-white border-primary shadow-xs' : 'bg-card border-border text-text-muted hover:text-text-primary'
              }`}
            >
              {opt}
            </button>
          ))}
        </div>
      </div>
    </motion.div>
  );
}

export default AccessibilitySettings;
