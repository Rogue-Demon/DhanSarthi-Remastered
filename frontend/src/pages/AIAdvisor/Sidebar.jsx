import React, { useState } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import * as LucideIcons from 'lucide-react'
import { cn } from '@/utils'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import { Badge, Button } from '@/components/ui'
import { useConversationList, useCreateConversation } from '@/hooks/useAI'

/**
 * AI Advisor Sidebar
 *
 * Shows real conversations from the backend.
 * "New Conversation" creates a real conversation thread and navigates to it.
 * Collapses into a mobile drawer with AnimatePresence.
 */
export function Sidebar({ isOpen, onClose, className }) {
  const location = useLocation()
  const navigate = useNavigate()
  const shouldReduceMotion = useReducedMotion()
  const [search, setSearch] = useState('')

  // ── Real backend data ─────────────────────────────────────────────────────
  const { data: convList, isLoading } = useConversationList({ limit: 30 })
  const conversations = convList?.items ?? []

  const createMutation = useCreateConversation()

  // ── Helpers ───────────────────────────────────────────────────────────────
  const navItems = [
    { label: 'Chat', path: '/ai-advisor/chat', icon: 'MessageSquare' },
    { label: 'History', path: '/ai-advisor/history', icon: 'History' },
    { label: 'Saved', path: '/ai-advisor/saved', icon: 'Bookmark' },
    { label: 'Templates', path: '/ai-advisor/templates', icon: 'FileText' },
    { label: 'Settings', path: '/ai-advisor/settings', icon: 'Settings' },
  ]

  const isActivePath = (path) => {
    if (path === '/ai-advisor/chat') {
      return location.pathname === '/ai-advisor' || location.pathname.startsWith('/ai-advisor/chat')
    }
    return location.pathname === path
  }

  const filtered = conversations.filter((c) => c.title.toLowerCase().includes(search.toLowerCase()))

  const handleNewConversation = () => {
    createMutation.mutate(
      { title: null },
      {
        onSuccess: (data) => {
          if (onClose) onClose()
          navigate(`/ai-advisor/chat/${data.id}`)
        },
      }
    )
  }

  const handleOpenConversation = (id) => {
    if (onClose) onClose()
    navigate(`/ai-advisor/chat/${id}`)
  }

  const formatDate = (isoString) => {
    if (!isoString) return ''
    const d = new Date(isoString)
    const now = new Date()
    const diffDays = Math.floor((now - d) / 86_400_000)
    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return `${diffDays}d ago`
    return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
  }

  // Show first 2 as "pinned" (most recent), rest as "recent"
  const pinned = filtered.slice(0, 2)
  const recent = filtered.slice(2, 5)

  const sidebarContent = (
    <div className="flex flex-col h-full gap-4 p-4 overflow-y-auto scrollbar-none">
      {/* New Chat CTA */}
      <Button
        variant="gradient"
        size="sm"
        className="w-full rounded-xl font-black text-xs gap-2 shadow-button"
        onClick={handleNewConversation}
        disabled={createMutation.isPending}
        iconLeft={
          createMutation.isPending ? (
            <LucideIcons.Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <LucideIcons.Plus className="h-4 w-4" />
          )
        }
      >
        {createMutation.isPending ? 'Creating…' : 'New Conversation'}
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
          const Icon = LucideIcons[item.icon] || LucideIcons.Layers
          const active = isActivePath(item.path)
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
              <Icon
                className={cn(
                  'h-4 w-4 stroke-[2.2] shrink-0',
                  active ? 'text-primary' : 'text-text-muted'
                )}
              />
              <span>{item.label}</span>
            </NavLink>
          )
        })}
      </nav>

      {/* Divider */}
      <div className="border-t border-border/60" />

      {/* Loading skeleton */}
      {isLoading && (
        <div className="flex flex-col gap-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-start gap-2.5 p-2.5 rounded-xl">
              <div className="h-3.5 w-3.5 rounded bg-muted animate-pulse shrink-0 mt-0.5" />
              <div className="flex flex-col gap-1 flex-1">
                <div className="h-3 w-3/4 rounded bg-muted animate-pulse" />
                <div className="h-2.5 w-1/2 rounded bg-muted animate-pulse" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pinned (recent) Conversations */}
      {!isLoading && pinned.length > 0 && (
        <div className="flex flex-col gap-2">
          <span className="text-[9px] font-black text-text-muted uppercase tracking-widest px-1">
            Recent ({pinned.length})
          </span>
          {pinned.map((conv) => (
            <button
              key={conv.id}
              className="flex items-start gap-2.5 p-2.5 rounded-xl text-left hover:bg-muted/40 transition-colors group cursor-pointer w-full"
              onClick={() => handleOpenConversation(conv.id)}
            >
              <LucideIcons.MessageSquare className="h-3.5 w-3.5 text-primary shrink-0 mt-0.5" />
              <div className="flex flex-col gap-0.5 overflow-hidden flex-1">
                <span className="text-xs font-black text-text-primary truncate group-hover:text-primary transition-colors">
                  {conv.title}
                </span>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold text-text-muted">
                    {formatDate(conv.updated_at)}
                  </span>
                  {conv.message_count > 0 && (
                    <span className="text-[9px] font-bold text-text-muted">
                      {conv.message_count} msgs
                    </span>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Older Conversations */}
      {!isLoading && recent.length > 0 && (
        <div className="flex flex-col gap-2">
          <span className="text-[9px] font-black text-text-muted uppercase tracking-widest px-1">
            Older
          </span>
          {recent.map((conv) => (
            <button
              key={conv.id}
              className="flex items-start gap-2.5 p-2.5 rounded-xl text-left hover:bg-muted/40 transition-colors group cursor-pointer w-full"
              onClick={() => handleOpenConversation(conv.id)}
            >
              <LucideIcons.MessageSquare className="h-3.5 w-3.5 text-text-muted shrink-0 mt-0.5" />
              <div className="flex flex-col gap-0.5 overflow-hidden">
                <span className="text-xs font-bold text-text-primary truncate group-hover:text-primary transition-colors">
                  {conv.title}
                </span>
                <span className="text-[10px] font-bold text-text-muted">
                  {formatDate(conv.updated_at)}
                </span>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!isLoading && filtered.length === 0 && (
        <div className="flex flex-col items-center gap-2 py-4 text-center">
          <LucideIcons.MessageSquarePlus className="h-8 w-8 text-text-muted/40" />
          <span className="text-[10px] font-bold text-text-muted">
            {search ? 'No matching conversations' : 'No conversations yet'}
          </span>
        </div>
      )}

      {/* Footer count */}
      {!isLoading && conversations.length > 0 && (
        <div className="mt-auto pt-4 border-t border-border/40">
          <span className="text-[10px] font-bold text-text-muted">
            {convList?.total ?? conversations.length} conversation
            {(convList?.total ?? conversations.length) !== 1 ? 's' : ''} total
          </span>
        </div>
      )}
    </div>
  )

  return (
    <>
      {/* Desktop Sidebar */}
      <aside
        className={cn(
          'hidden md:flex flex-col w-64 shrink-0 bg-card border-r border-border/80 h-full overflow-hidden',
          className
        )}
      >
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
                <span className="text-sm font-black text-text-primary uppercase tracking-wider">
                  Conversations
                </span>
                <button
                  onClick={onClose}
                  className="p-1.5 rounded-lg hover:bg-muted/40 text-text-muted"
                >
                  <LucideIcons.X className="h-4 w-4" />
                </button>
              </div>
              {sidebarContent}
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  )
}

export default Sidebar
