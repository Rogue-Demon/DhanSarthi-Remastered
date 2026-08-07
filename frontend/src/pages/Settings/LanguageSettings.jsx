import React, { useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import * as LucideIcons from 'lucide-react';

const LANGUAGES = [
  { code: 'en', name: 'English', native: 'English', flag: '🇺🇸' },
  { code: 'hi', name: 'Hindi', native: 'हिन्दी', flag: '🇮🇳' },
  { code: 'mr', name: 'Marathi', native: 'मराठी', flag: '🇮🇳' },
  { code: 'ta', name: 'Tamil', native: 'தமிழ்', flag: '🇮🇳' },
  { code: 'bn', name: 'Bengali', native: 'বাংলা', flag: '🇮🇳' },
  { code: 'gu', name: 'Gujarati', native: 'ગુજરાતી', flag: '🇮🇳' },
  { code: 'te', name: 'Telugu', native: 'తెలుగు', flag: '🇮🇳' },
  { code: 'kn', name: 'Kannada', native: 'ಕನ್ನಡ', flag: '🇮🇳' },
];

export function LanguageSettings() {
  const shouldReduceMotion = useReducedMotion();
  const [selected, setSelected] = useState('en');

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 w-full text-left select-none max-w-3xl mx-auto"
    >
      <div className="flex flex-col gap-1">
        <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">Language & Region</h3>
        <p className="text-xs font-bold text-text-muted">Select your preferred display language. Content will be localised accordingly.</p>
      </div>

      <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl shadow-xs">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {LANGUAGES.map((lang) => (
            <button
              key={lang.code}
              onClick={() => setSelected(lang.code)}
              className={`flex items-center gap-3 p-4 rounded-xl border transition-all cursor-pointer ${
                selected === lang.code
                  ? 'bg-primary/10 border-primary text-primary shadow-xs'
                  : 'bg-muted/20 border-border/60 text-text-muted hover:text-text-primary hover:border-primary/40'
              }`}
            >
              <span className="text-xl">{lang.flag}</span>
              <div className="flex flex-col text-left gap-0">
                <span className="text-xs font-black">{lang.name}</span>
                <span className="text-[10px] font-bold opacity-70">{lang.native}</span>
              </div>
              {selected === lang.code && <LucideIcons.Check className="h-4 w-4 ml-auto text-primary" />}
            </button>
          ))}
        </div>
      </div>

      <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl shadow-xs flex items-center gap-3">
        <LucideIcons.Info className="h-4 w-4 text-primary shrink-0" />
        <p className="text-[10px] font-bold text-text-muted">
          Language support is in progress. Currently only English is fully available; switching to other languages will localise headings and labels where translations exist.
        </p>
      </div>
    </motion.div>
  );
}

export default LanguageSettings;
