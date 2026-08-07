import React, { useState } from 'react';
import { useProfile } from '@/hooks';
import { motion, useReducedMotion } from 'framer-motion';
import { Badge, Button } from '@/components/ui';
import * as LucideIcons from 'lucide-react';

export function Settings() {
  const { profile } = useProfile();
  const shouldReduceMotion = useReducedMotion();

  const [tone, setTone] = useState('Friendly');
  const [language, setLanguage] = useState('English');
  const [length, setLength] = useState('Detailed');

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 p-4 md:p-6 w-full h-full overflow-y-auto scrollbar-none text-left select-none max-w-3xl mx-auto"
    >
      <div className="flex flex-col gap-1">
        <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">
          AI Advisor Preferences
        </h3>
        <p className="text-xs font-bold text-text-muted">
          Customize AI assistant tone, language, response formats, and financial context parameters.
        </p>
      </div>

      <div className="flex flex-col gap-6">
        
        {/* Preferred Tone */}
        <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl flex flex-col gap-3 shadow-xs">
          <div className="flex flex-col gap-1">
            <span className="text-xs font-black text-text-primary uppercase tracking-wider">Advisor Tone</span>
            <span className="text-[10px] font-bold text-text-muted">Select how the AI financial advisor communicates with you.</span>
          </div>
          <div className="grid grid-cols-3 gap-2 pt-1">
            {['Professional', 'Friendly', 'Concise'].map((t) => (
              <button
                key={t}
                onClick={() => setTone(t)}
                className={`py-2 px-3 rounded-xl text-xs font-black uppercase tracking-wider transition-all cursor-pointer border ${
                  tone === t
                    ? 'bg-primary text-white border-primary shadow-xs'
                    : 'bg-card border-border text-text-muted hover:text-text-primary'
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>

        {/* Preferred Language */}
        <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl flex flex-col gap-3 shadow-xs">
          <div className="flex flex-col gap-1">
            <span className="text-xs font-black text-text-primary uppercase tracking-wider">Response Language</span>
            <span className="text-[10px] font-bold text-text-muted">Language used for financial advice and reports.</span>
          </div>
          <div className="grid grid-cols-3 gap-2 pt-1">
            {['English', 'Hindi', 'Hinglish'].map((l) => (
              <button
                key={l}
                onClick={() => setLanguage(l)}
                className={`py-2 px-3 rounded-xl text-xs font-black uppercase tracking-wider transition-all cursor-pointer border ${
                  language === l
                    ? 'bg-primary text-white border-primary shadow-xs'
                    : 'bg-card border-border text-text-muted hover:text-text-primary'
                }`}
              >
                {l}
              </button>
            ))}
          </div>
        </div>

        {/* Response Length */}
        <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl flex flex-col gap-3 shadow-xs">
          <div className="flex flex-col gap-1">
            <span className="text-xs font-black text-text-primary uppercase tracking-wider">Detail Level</span>
            <span className="text-[10px] font-bold text-text-muted">Choose between bullet points or step-by-step financial explanations.</span>
          </div>
          <div className="grid grid-cols-2 gap-2 pt-1">
            {['Bullet Summary', 'Detailed'].map((len) => (
              <button
                key={len}
                onClick={() => setLength(len)}
                className={`py-2 px-3 rounded-xl text-xs font-black uppercase tracking-wider transition-all cursor-pointer border ${
                  length === len
                    ? 'bg-primary text-white border-primary shadow-xs'
                    : 'bg-card border-border text-text-muted hover:text-text-primary'
                }`}
              >
                {len}
              </button>
            ))}
          </div>
        </div>

        {/* Privacy & Data Controls */}
        <div className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 rounded-2xl flex flex-col gap-4 shadow-xs">
          <div className="flex flex-col gap-1">
            <span className="text-xs font-black text-text-primary uppercase tracking-wider">Privacy & Account Data</span>
            <span className="text-[10px] font-bold text-text-muted">Manage conversation history and export local AI logs.</span>
          </div>

          <div className="flex flex-wrap items-center gap-3 pt-1">
            <Button
              variant="secondary"
              size="sm"
              className="rounded-xl font-bold text-xs gap-1.5 border-border text-text-primary bg-card"
              onClick={() => alert('Export conversation history')}
              iconLeft={<LucideIcons.Download className="h-4 w-4" />}
            >
              Export Chat History
            </Button>

            <Button
              variant="ghost"
              size="sm"
              className="rounded-xl font-bold text-xs gap-1.5 text-danger hover:bg-danger/10"
              onClick={() => alert('Reset AI state placeholder')}
              iconLeft={<LucideIcons.RotateCcw className="h-4 w-4" />}
            >
              Clear Conversation History
            </Button>
          </div>
        </div>

      </div>
    </motion.div>
  );
}

export default Settings;
