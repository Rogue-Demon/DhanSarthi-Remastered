import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import * as LucideIcons from 'lucide-react';
import { cn } from '@/utils';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { placeholderConversations } from '@/config';
import { Badge, Button } from '@/components/ui';

/**
 * AI Advisor Sidebar
 *
 * Conversation list sidebar with new chat, search, pinned/recent conversations,
 * and navigation tabs. Collapses into a mobile drawer with AnimatePresence.
 */
export function Sidebar({ isOpen, onClose, className }) {
  const location = useLocation();
  const shouldReduceMotion = useReducedMotion();
  const [search, setSearch] = useState('');

  const navItems = [
    { label: 'Chat', path: '/ai-advisor/chat', icon: 'MessageSquare' },
    { label: 'History', path: '/ai-advisor/history', icon: 'History' },
    { label: 'Saved', path: '/ai-advisor/saved', icon: 'Bookmark' },
    { label: 'Templates', path: '/ai-advisor/templates', icon: 'FileText' },
    { label: 'Settings', path: '/ai-advisor/settings', icon: 'Settings' },
  ];

  const isActivePath = (path) => {
    if (path === '/ai-advisor/chat') {
      return location.pathname === '/ai-advisor' || location.pathname === '/ai-advisor/chat';
    }
    return location.pathname === path;
  };

  const pinned = placeholderConversations.filter((c) => c.pinned);
  const recent = placeholderConversations.filter((c) => !c.pinned).slice(0, 3);

  const sidebarContent = (
    <div className="flex flex-col h-full gap-4 p-4 overflow-y-auto scrollbar-none">
      {/* New Chat CTA */}
      <Button
        variant="gradient"
        size="sm"
        className="w-full rounded-xl font-black text-xs gap-2 shadow-button"
        onClick={() => console.log('New conversation')}
        iconLeft={<LucideIcons.Plus className="h-4 w-4" />}
      >
        New Conversation
      </Button>

      {/* Search */}
      <div className="relative">
        <LucideIcons.Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-text-muted" />
        <input
          type="text"
          placeholder="Search chats..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-9 pr-3 py-2 text-xs font-bold rounded-xl border border-border bg-card/60 text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary/40 transition-colors"
        />
      </div>

      {/* Navigation Links */}
      <nav className="flex flex-col gap-1">
        {navItems.map((item) => {
          const Icon = LucideIcons[item.icon] || LucideIcons.Layers;
          const active = isActivePath(item.path);

          return (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={onClose}
              className={cn(
                'relative flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-black uppercase tracking-wider transition-all duration-200 outline-none group',
                active
                  ? 'text-primary bg-primary/10'
                  : 'text-text-muted hover:text-text-secondary hover:bg-muted/40'
              )}
            >
              <Icon className={cn('h-4 w-4 stroke-[2.2] shrink-0', active ? 'text-primary' : 'text-text-muted')} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Divider */}
      <div className="border-t border-border/60" />

      {/* Pinned Conversations */}
      {pinned.length > 0 && (
        <div className="flex flex-col gap-2">
          <span className="text-[9px] font-black text-text-muted uppercase tracking-widest px-1">
            Pinned ({pinned.length})
          </span>
          {pinned.map((conv) => (
            <button
              key={conv.id}
              className="flex items-start gap-2.5 p-2.5 rounded-xl text-left hover:bg-muted/40 transition-colors group cursor-pointer w-full"
              onClick={() => console.log('Open conversation', conv.id)}
            >
              <LucideIcons.Pin className="h-3.5 w-3.5 text-primary shrink-0 mt-0.5" />
              <div className="flex flex-col gap-0.5 overflow-hidden">
                <span className="text-xs font-black text-text-primary truncate group-hover:text-primary transition-colors">
                  {conv.title}
                </span>
                <span className="text-[10px] font-bold text-text-muted truncate">
                  {conv.preview.slice(0, 40)}...
                </span>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Recent Conversations */}
      {recent.length > 0 && (
        <div className="flex flex-col gap-2">
          <span className="text-[9px] font-black text-text-muted uppercase tracking-widest px-1">
            Recent
          </span>
          {recent.map((conv) => (
            <button
              key={conv.id}
              className="flex items-start gap-2.5 p-2.5 rounded-xl text-left hover:bg-muted/40 transition-colors group cursor-pointer w-full"
              onClick={() => console.log('Open conversation', conv.id)}
            >
              <LucideIcons.MessageSquare className="h-3.5 w-3.5 text-text-muted shrink-0 mt-0.5" />
              <div className="flex flex-col gap-0.5 overflow-hidden">
                <span className="text-xs font-bold text-text-primary truncate group-hover:text-primary transition-colors">
                  {conv.title}
                </span>
                <span className="text-[10px] font-bold text-text-muted">
                  {conv.date}
                </span>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Conversation Count Footer */}
      <div className="mt-auto pt-4 border-t border-border/40">
        <span className="text-[10px] font-bold text-text-muted">
          {placeholderConversations.length} conversations total
        </span>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Sidebar */}
      <aside className={cn('hidden md:flex flex-col w-64 shrink-0 bg-card border-r border-border/80 h-full overflow-hidden', className)}>
        {sidebarContent}
      </aside>

      {/* Mobile Drawer Overlay */}
      <AnimatePresence>
        {isOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40 md:hidden"
              onClick={onClose}
            />
            <motion.aside
              initial={{ x: shouldReduceMotion ? 0 : -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              className="fixed left-0 top-0 bottom-0 w-72 bg-card border-r border-border z-50 md:hidden shadow-floating overflow-hidden"
            >
              <div className="flex items-center justify-between p-4 border-b border-border/60">
                <span className="text-sm font-black text-text-primary uppercase tracking-wider">Conversations</span>
                <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-muted/40 text-text-muted">
                  <LucideIcons.X className="h-4 w-4" />
                </button>
              </div>
              {sidebarContent}
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
}

export default Sidebar;
