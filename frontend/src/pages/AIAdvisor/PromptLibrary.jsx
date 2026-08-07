import React, { useState } from 'react';
import * as LucideIcons from 'lucide-react';
import { promptLibrary } from '@/config';
import { motion, useReducedMotion } from 'framer-motion';
import { Badge } from '@/components/ui';

/**
 * PromptLibrary Component
 * Categorized library of finance prompts with quick-select cards.
 */
export function PromptLibrary({ onSelectPrompt }) {
  const shouldReduceMotion = useReducedMotion();
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [search, setSearch] = useState('');

  const categories = ['All', ...promptLibrary.map((c) => c.category)];

  const filteredCategories = promptLibrary.filter((cat) => {
    if (selectedCategory !== 'All' && cat.category !== selectedCategory) return false;
    if (!search) return true;
    return (
      cat.category.toLowerCase().includes(search.toLowerCase()) ||
      cat.prompts.some((p) => p.toLowerCase().includes(search.toLowerCase()))
    );
  });

  return (
    <div className="flex flex-col gap-6 w-full text-left select-none">
      {/* Search & Filter Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">
            Prompt Library
          </h3>
          <p className="text-xs font-bold text-text-muted">
            Curated prompt templates for financial planning, budgeting, and tax optimization.
          </p>
        </div>

        {/* Search Input */}
        <div className="relative w-full sm:w-64">
          <LucideIcons.Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-text-muted" />
          <input
            type="text"
            placeholder="Search prompts..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-xs font-bold rounded-xl border border-border bg-card text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary/40 transition-colors"
          />
        </div>
      </div>

      {/* Category Pills */}
      <div className="flex items-center gap-2 overflow-x-auto scrollbar-none pb-1">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-3 py-1.5 rounded-xl text-xs font-black uppercase tracking-wider shrink-0 transition-all cursor-pointer ${
              selectedCategory === cat
                ? 'bg-primary text-white shadow-xs'
                : 'bg-card border border-border text-text-muted hover:text-text-primary hover:bg-muted/40'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Prompt Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredCategories.map((catGroup) => {
          const Icon = LucideIcons[catGroup.icon] || LucideIcons.HelpCircle;

          return catGroup.prompts.map((promptText, idx) => (
            <motion.div
              key={`${catGroup.category}-${idx}`}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.03 }}
              onClick={() => onSelectPrompt && onSelectPrompt(promptText)}
              className="clay-surface bg-card p-4 border border-white/60 dark:border-white/5 shadow-card hover:border-primary/30 transition-all cursor-pointer flex flex-col justify-between gap-3 group h-full"
            >
              <div className="flex items-center gap-2.5">
                <div
                  className="p-2 rounded-xl flex items-center justify-center shrink-0 border shadow-xs"
                  style={{
                    background: `${catGroup.color}12`,
                    color: catGroup.color,
                    borderColor: `${catGroup.color}25`,
                  }}
                >
                  <Icon className="h-4 w-4 stroke-[2.2]" />
                </div>
                <Badge variant="secondary" className="text-[8px] font-bold py-0.5 px-1.5 rounded" style={{ color: catGroup.color }}>
                  {catGroup.category}
                </Badge>
              </div>

              <p className="text-xs font-bold text-text-primary group-hover:text-primary transition-colors leading-relaxed">
                "{promptText}"
              </p>

              <div className="flex items-center justify-between text-[10px] font-black text-primary opacity-0 group-hover:opacity-100 transition-opacity pt-1">
                <span>Use Prompt</span>
                <LucideIcons.ArrowRight className="h-3 w-3" />
              </div>
            </motion.div>
          ));
        })}
      </div>
    </div>
  );
}

export default PromptLibrary;
