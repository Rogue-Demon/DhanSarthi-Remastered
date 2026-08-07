import React, { useState } from 'react';
import { placeholderConversations } from '@/config';
import { motion, useReducedMotion } from 'framer-motion';
import { Badge, Button } from '@/components/ui';
import * as LucideIcons from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function History() {
  const shouldReduceMotion = useReducedMotion();
  const navigate = useNavigate();
  const [search, setSearch] = useState('');

  const filtered = placeholderConversations.filter((c) =>
    c.title.toLowerCase().includes(search.toLowerCase()) ||
    c.preview.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col gap-6 p-4 md:p-6 w-full h-full overflow-y-auto scrollbar-none text-left select-none max-w-4xl mx-auto"
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h3 className="text-lg font-black text-text-primary uppercase tracking-wider leading-none">
            Conversation History
          </h3>
          <p className="text-xs font-bold text-text-muted">
            View, search, and manage your past AI Financial Advisor chats.
          </p>
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-64">
          <LucideIcons.Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-text-muted" />
          <input
            type="text"
            placeholder="Search history..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-xs font-bold rounded-xl border border-border bg-card text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary/40 transition-colors"
          />
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="clay-surface bg-card border-2 border-white/60 rounded-3xl p-10 shadow-floating text-center flex flex-col items-center justify-center gap-4 max-w-md mx-auto my-10">
          <div className="h-14 w-14 rounded-2xl bg-muted border flex items-center justify-center text-text-muted">
            <LucideIcons.History className="h-7 w-7" />
          </div>
          <div className="flex flex-col gap-1">
            <h4 className="text-sm font-black text-text-primary uppercase tracking-wider">No History Found</h4>
            <p className="text-xs font-bold text-text-muted max-w-[280px] leading-relaxed mt-1">
              No previous conversations match your search criteria.
            </p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((conv, idx) => (
            <motion.div
              key={conv.id}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.04 }}
              className="clay-surface bg-card p-5 border border-white/60 dark:border-white/5 shadow-card hover:border-primary/30 transition-all flex flex-col justify-between gap-4 group text-left"
            >
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-black text-text-primary group-hover:text-primary transition-colors">
                    {conv.title}
                  </span>
                  <div className="flex items-center gap-1.5">
                    {conv.pinned && (
                      <LucideIcons.Pin className="h-3.5 w-3.5 text-primary" title="Pinned" />
                    )}
                    {conv.favorite && (
                      <LucideIcons.Star className="h-3.5 w-3.5 text-warning fill-warning" title="Favorite" />
                    )}
                  </div>
                </div>

                <p className="text-xs font-medium text-text-muted leading-relaxed line-clamp-2">
                  "{conv.preview}"
                </p>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-border/40 text-[10px] font-bold text-text-muted">
                <span>{conv.date}</span>
                <Button
                  variant="ghost"
                  size="xs"
                  className="p-0 text-primary font-black uppercase tracking-wider hover:bg-transparent"
                  onClick={() => navigate('/ai-advisor/chat')}
                  iconRight={<LucideIcons.ArrowRight className="h-3 w-3" />}
                >
                  Open Chat
                </Button>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </motion.div>
  );
}

export default History;
