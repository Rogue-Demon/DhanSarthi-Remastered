import React, { useState } from 'react';
import { aiTemplates } from '@/config';
import { motion, useReducedMotion } from 'framer-motion';
import { Badge, Button } from '@/components/ui';
import * as LucideIcons from 'lucide-react';
import PromptLibrary from './PromptLibrary';
import { useNavigate } from 'react-router-dom';

export function Templates() {
  const shouldReduceMotion = useReducedMotion();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('templates'); // 'templates' | 'library'

  const handleUseTemplate = (title) => {
    navigate('/ai-advisor/chat');
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 p-4 md:p-6 w-full h-full overflow-y-auto scrollbar-none text-left select-none max-w-5xl mx-auto"
    >
      {/* Header & Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">
            AI Prompts & Templates
          </h3>
          <p className="text-xs font-bold text-text-muted">
            Pre-built financial workflows, budget planners, and advisory templates.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-card border border-border shrink-0 self-start sm:self-center">
          <button
            onClick={() => setActiveTab('templates')}
            className={`px-3 py-1.5 rounded-lg text-xs font-black uppercase tracking-wider transition-all cursor-pointer ${
              activeTab === 'templates' ? 'bg-primary text-white shadow-xs' : 'text-text-muted hover:text-text-primary'
            }`}
          >
            Templates ({aiTemplates.length})
          </button>
          <button
            onClick={() => setActiveTab('library')}
            className={`px-3 py-1.5 rounded-lg text-xs font-black uppercase tracking-wider transition-all cursor-pointer ${
              activeTab === 'library' ? 'bg-primary text-white shadow-xs' : 'text-text-muted hover:text-text-primary'
            }`}
          >
            Prompt Library
          </button>
        </div>
      </div>

      {activeTab === 'templates' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {aiTemplates.map((tpl, idx) => {
            const Icon = LucideIcons[tpl.icon] || LucideIcons.FileText;

            return (
              <motion.div
                key={tpl.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: idx * 0.04 }}
                className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 shadow-card hover:border-primary/30 transition-all flex flex-col justify-between gap-4 group text-left h-full"
              >
                <div className="flex flex-col gap-3">
                  <div className="flex items-center gap-3">
                    <div
                      className="p-2.5 rounded-xl flex items-center justify-center shrink-0 border shadow-xs"
                      style={{
                        background: `${tpl.color}12`,
                        color: tpl.color,
                        borderColor: `${tpl.color}25`,
                      }}
                    >
                      <Icon className="h-5 w-5 stroke-[2.2]" />
                    </div>
                    <span className="text-sm font-black text-text-primary group-hover:text-primary transition-colors">
                      {tpl.title}
                    </span>
                  </div>

                  <p className="text-xs font-semibold text-text-muted leading-relaxed">
                    {tpl.desc}
                  </p>
                </div>

                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => handleUseTemplate(tpl.title)}
                  className="w-full rounded-xl font-bold text-xs justify-center border-border hover:border-primary/30 text-text-primary bg-card"
                  iconRight={<LucideIcons.ArrowRight className="h-3.5 w-3.5" />}
                >
                  Use Template
                </Button>
              </motion.div>
            );
          })}
        </div>
      ) : (
        <PromptLibrary onSelectPrompt={() => navigate('/ai-advisor/chat')} />
      )}
    </motion.div>
  );
}

export default Templates;
