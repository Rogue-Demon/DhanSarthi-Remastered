import React, { useState, useRef, useEffect, useCallback } from 'react'
import { useProfile } from '@/hooks'
import { useConversationDetail, useSendMessage } from '@/hooks/useAI'
import { getAIAdvisorConfig } from '@/config'
import { motion, useReducedMotion } from 'framer-motion'
import { Badge, Button } from '@/components/ui'
import * as LucideIcons from 'lucide-react'
import { cn } from '@/utils'

/**
 * ChatWorkspace Component
 *
 * Full-featured interactive chat interface connected to the real AI Advisor backend.
 *
 * Props:
 *   conversationId (number|null) — if provided, loads and continues an existing conversation.
 *                                   if null/undefined, shows the welcome screen (no conversation yet).
 *   initialPrompt (string)       — pre-fill the input text field.
 *
 * State model:
 *   - Conversation messages come from `useConversationDetail` (real backend data).
 *   - Sending uses `useSendMessage` mutation — backend returns both user + assistant messages.
 *   - Optimistic user message is appended immediately so the UI feels instant.
 *   - On mutation success the query is invalidated and real data re-fetches.
 */
export function ChatWorkspace({ conversationId = null, initialPrompt = '' }) {
  const { profile } = useProfile()
  const shouldReduceMotion = useReducedMotion()
  const advisorConfig = getAIAdvisorConfig(profile)

  const [inputText, setInputText] = useState(initialPrompt || '')
  // Optimistic messages shown while the real response is loading
  const [optimisticMessages, setOptimisticMessages] = useState([])
  const [expandedCalcMsgId, setExpandedCalcMsgId] = useState(null)
  const messagesEndRef = useRef(null)

  // ── Real data: load conversation messages when conversationId is set ──────
  const { data: convDetail, isLoading: isLoadingHistory } = useConversationDetail(conversationId)

  // ── Send message mutation ─────────────────────────────────────────────────
  const sendMutation = useSendMessage(conversationId)

  // Auto-scroll to bottom when messages change
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [convDetail, optimisticMessages, sendMutation.isPending, scrollToBottom])

  // ── Build the displayed message list ─────────────────────────────────────
  // Real messages from backend (chronological); append optimistic messages while pending
  const realMessages = convDetail?.messages ?? []
  const displayMessages = sendMutation.isPending
    ? [...realMessages, ...optimisticMessages]
    : realMessages

  // ── Handlers ─────────────────────────────────────────────────────────────
  const handleSend = () => {
    const text = inputText.trim()
    if (!text || !conversationId || sendMutation.isPending) return

    // Optimistic user message (will be replaced by real data after mutation)
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    setOptimisticMessages([
      {
        id: `opt-u-${Date.now()}`,
        role: 'USER',
        content: text,
        created_at: now,
        _optimistic: true,
      },
    ])
    setInputText('')

    sendMutation.mutate({ message: text })
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handlePromptClick = (promptText) => {
    setInputText(promptText)
  }

  const handleCopy = (content) => {
    navigator.clipboard?.writeText(content).catch(() => {})
  }

  // ── Welcome screen (no conversation loaded yet) ───────────────────────────
  if (!conversationId) {
    return (
      <div className="flex flex-col h-full w-full bg-background overflow-hidden relative select-none">
        <div className="flex-1 overflow-y-auto p-4 md:p-6 scrollbar-none">
          <div className="flex flex-col items-center justify-center min-h-[70%] text-center max-w-2xl mx-auto gap-6 my-auto py-10">
            <div className="h-16 w-16 rounded-3xl bg-gradient-primary flex items-center justify-center text-white shadow-floating">
              <LucideIcons.Sparkles className="h-8 w-8 animate-pulse" />
            </div>
            <div className="flex flex-col gap-2">
              <Badge
                variant="secondary"
                className="mx-auto text-[10px] font-black uppercase tracking-widest bg-primary/10 text-primary border-primary/20 py-0.5 px-3 rounded-full"
              >
                AI Financial Workspace
              </Badge>
              <h3 className="text-2xl md:text-3xl font-black text-text-primary tracking-tight">
                {advisorConfig.welcome.greeting}
              </h3>
              <p className="text-xs md:text-sm font-semibold text-text-muted leading-relaxed max-w-lg">
                {advisorConfig.welcome.description}
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 w-full pt-4">
              {advisorConfig.suggestedPrompts.map((prompt, idx) => {
                const Icon = LucideIcons[prompt.icon] || LucideIcons.HelpCircle
                return (
                  <motion.button
                    key={idx}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    onClick={() => handlePromptClick(prompt.text)}
                    className="clay-surface bg-card p-4 border border-white/60 dark:border-white/5 shadow-card hover:border-primary/30 transition-all text-left flex items-start gap-3 group cursor-pointer"
                  >
                    <div className="p-2 rounded-xl bg-primary/10 text-primary shrink-0">
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="flex flex-col gap-0.5">
                      <span className="text-[9px] font-black text-text-muted uppercase tracking-wider">
                        {prompt.category}
                      </span>
                      <span className="text-xs font-bold text-text-primary group-hover:text-primary transition-colors">
                        {prompt.text}
                      </span>
                    </div>
                  </motion.button>
                )
              })}
            </div>
            <p className="text-[10px] font-bold text-text-muted mt-2">
              Select a conversation from the sidebar or start a new one to begin.
            </p>
          </div>
        </div>
      </div>
    )
  }

  // ── Chat view (conversation loaded) ──────────────────────────────────────
  return (
    <div className="flex flex-col h-full w-full bg-background overflow-hidden relative select-none">
      {/* Scrollable Chat Area */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 scrollbar-none">
        {/* Loading history skeleton */}
        {isLoadingHistory && (
          <div className="flex flex-col gap-4 max-w-3xl mx-auto w-full pt-6">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className={cn(
                  'flex items-start gap-3',
                  i % 2 === 0 ? 'flex-row-reverse' : 'flex-row'
                )}
              >
                <div className="h-8 w-8 rounded-xl bg-muted animate-pulse shrink-0" />
                <div
                  className={cn('flex flex-col gap-2', i % 2 === 0 ? 'items-end' : 'items-start')}
                >
                  <div className="h-3 w-20 rounded bg-muted animate-pulse" />
                  <div className="h-16 w-64 rounded-2xl bg-muted animate-pulse" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty state for new conversation */}
        {!isLoadingHistory && displayMessages.length === 0 && (
          <div className="flex flex-col items-center justify-center min-h-[60%] text-center max-w-2xl mx-auto gap-4 py-10">
            <div className="h-14 w-14 rounded-2xl bg-primary/10 flex items-center justify-center text-primary">
              <LucideIcons.MessageSquare className="h-7 w-7" />
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-sm font-black text-text-primary uppercase tracking-wider">
                Ready to Advise
              </span>
              <p className="text-xs font-bold text-text-muted max-w-xs">
                Ask DhanSarthi AI anything about your finances below.
              </p>
            </div>
            <div className="flex flex-wrap justify-center gap-2 pt-2">
              {advisorConfig.suggestedPrompts.slice(0, 3).map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => handlePromptClick(p.text)}
                  className="text-[10px] font-bold px-3 py-1.5 rounded-xl bg-primary/10 border border-primary/20 text-primary hover:bg-primary/20 transition-colors cursor-pointer"
                >
                  {p.text}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Messages List */}
        {!isLoadingHistory && displayMessages.length > 0 && (
          <div className="flex flex-col gap-5 max-w-3xl mx-auto w-full">
            {displayMessages.map((msg) => {
              const isUser = msg.role === 'USER' || msg.role === 'user'
              const timeStr = msg.created_at
                ? typeof msg.created_at === 'string' && msg.created_at.includes('T')
                  ? new Date(msg.created_at).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })
                  : msg.created_at
                : ''
              const meta = msg.message_metadata || msg.metadata || {}
              const citations = meta.citations ?? []
              const sources = meta.source_ids ?? []

              return (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={cn(
                    'flex items-start gap-3 w-full',
                    isUser ? 'flex-row-reverse' : 'flex-row'
                  )}
                >
                  {/* Avatar */}
                  <div
                    className={cn(
                      'h-8 w-8 rounded-xl flex items-center justify-center shrink-0 text-white font-black text-xs shadow-xs',
                      isUser ? 'bg-accent' : 'bg-gradient-primary'
                    )}
                  >
                    {isUser ? (
                      <LucideIcons.User className="h-4 w-4" />
                    ) : (
                      <LucideIcons.Bot className="h-4 w-4" />
                    )}
                  </div>

                  {/* Message Content */}
                  <div
                    className={cn(
                      'flex flex-col gap-1.5 max-w-[85%] text-left',
                      isUser ? 'items-end' : 'items-start'
                    )}
                  >
                    <div className="flex items-center gap-2 px-1">
                      <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                        {isUser ? 'You' : 'DhanSarthi AI'}
                      </span>
                      {timeStr && (
                        <span className="text-[9px] font-bold text-text-muted">{timeStr}</span>
                      )}
                      {msg._optimistic && (
                        <span className="text-[9px] font-bold text-text-muted italic">
                          sending…
                        </span>
                      )}
                    </div>

                    <div
                      className={cn(
                        'p-4 rounded-2xl text-xs md:text-sm font-medium leading-relaxed shadow-xs whitespace-pre-wrap',
                        isUser
                          ? 'bg-primary text-white rounded-tr-none'
                          : 'clay-surface bg-card border border-white/60 dark:border-white/5 text-text-primary rounded-tl-none'
                      )}
                    >
                      {msg.content}
                    </div>

                    {/* Assistant Action Toolbar */}
                    {!isUser && !msg._optimistic && (
                      <div className="flex items-center gap-1 pt-1 text-text-muted">
                        <button
                          className="p-1 rounded hover:bg-muted text-text-muted hover:text-text-primary"
                          title="Copy text"
                          onClick={() => handleCopy(msg.content)}
                        >
                          <LucideIcons.Copy className="h-3.5 w-3.5" />
                        </button>
                        <button
                          className="p-1 rounded hover:bg-muted text-text-muted hover:text-success"
                          title="Helpful"
                        >
                          <LucideIcons.ThumbsUp className="h-3.5 w-3.5" />
                        </button>
                        <button
                          className="p-1 rounded hover:bg-muted text-text-muted hover:text-danger"
                          title="Not helpful"
                        >
                          <LucideIcons.ThumbsDown className="h-3.5 w-3.5" />
                        </button>
                        <button
                          className="p-1 rounded hover:bg-muted text-text-muted hover:text-accent"
                          title="Bookmark"
                        >
                          <LucideIcons.Bookmark className="h-3.5 w-3.5" />
                        </button>
                        {meta.data_completeness && (
                          <span className="inline-flex items-center gap-1 text-[9px] font-bold text-emerald-600 bg-emerald-500/10 border border-emerald-500/20 rounded px-1.5 py-0.5">
                            <LucideIcons.CheckCircle2 className="h-3 w-3" />
                            <span>Based on your financial data</span>
                          </span>
                        )}
                        {meta.signals && meta.signals.length > 0 && (
                          <div className="flex items-center gap-1 flex-wrap">
                            {meta.signals.slice(0, 2).map((sig, idx) => (
                              <span
                                key={idx}
                                className="inline-flex items-center gap-1 text-[9px] font-bold text-amber-600 bg-amber-500/10 border border-amber-500/20 rounded px-1.5 py-0.5"
                                title={sig.evidence}
                              >
                                <LucideIcons.AlertTriangle className="h-2.5 w-2.5" />
                                <span>{sig.title}</span>
                              </span>
                            ))}
                          </div>
                        )}
                        {meta.health_score?.breakdown && meta.health_score.breakdown.length > 0 && (
                          <button
                            onClick={() =>
                              setExpandedCalcMsgId(expandedCalcMsgId === msg.id ? null : msg.id)
                            }
                            className="inline-flex items-center gap-1 text-[9px] font-bold text-primary bg-primary/10 border border-primary/20 rounded px-1.5 py-0.5 hover:bg-primary/20 transition-colors"
                          >
                            <LucideIcons.Calculator className="h-3 w-3" />
                            <span>How this was calculated</span>
                            <LucideIcons.ChevronDown
                              className={cn(
                                'h-2.5 w-2.5 transition-transform',
                                expandedCalcMsgId === msg.id && 'rotate-180'
                              )}
                            />
                          </button>
                        )}
                        {citations.length > 0 ? (
                          <div className="flex items-center gap-1.5 flex-wrap ml-1">
                            {citations.slice(0, 3).map((cit, idx) => (
                              <a
                                key={idx}
                                href={cit.source_url || '#'}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1 text-[9px] font-bold text-accent bg-accent/10 border border-accent/20 rounded px-1.5 py-0.5 hover:bg-accent/20 transition-colors"
                                title={cit.title}
                              >
                                <LucideIcons.ShieldCheck className="h-3 w-3" />
                                <span>
                                  {cit.authority || 'OFFICIAL'}: {cit.title}
                                </span>
                                {cit.source_url && (
                                  <LucideIcons.ExternalLink className="h-2.5 w-2.5 opacity-70" />
                                )}
                              </a>
                            ))}
                          </div>
                        ) : sources.length > 0 ? (
                          <span className="ml-1 text-[9px] font-bold text-text-muted border border-border/40 rounded px-1.5 py-0.5">
                            {sources.length} source{sources.length > 1 ? 's' : ''}
                          </span>
                        ) : null}
                      </div>
                    )}

                    {/* How Was This Calculated Accordion */}
                    {!isUser && expandedCalcMsgId === msg.id && meta.health_score?.breakdown && (
                      <div className="w-full mt-2 p-3 bg-muted/30 border border-border/60 rounded-xl flex flex-col gap-2 text-xs">
                        <div className="flex items-center justify-between font-bold text-text-primary border-b border-border/40 pb-1.5">
                          <span className="flex items-center gap-1.5">
                            <LucideIcons.Calculator className="h-3.5 w-3.5 text-primary" />
                            Deterministic Calculation Breakdown
                          </span>
                          {meta.health_score.overall_score !== null && (
                            <span className="text-[10px] bg-primary/10 text-primary px-2 py-0.5 rounded-full font-black">
                              Score: {meta.health_score.overall_score}/100 (
                              {meta.health_score.status})
                            </span>
                          )}
                        </div>
                        <div className="flex flex-col gap-2 pt-1">
                          {meta.health_score.breakdown.map((item, idx) => (
                            <div
                              key={idx}
                              className="flex flex-col gap-0.5 bg-card/60 p-2 rounded-lg border border-border/30"
                            >
                              <div className="flex justify-between items-center font-bold text-[11px] text-text-primary">
                                <span>{item.dimension}</span>
                                <span className="text-text-muted">
                                  Weight: {item.weight_percent}% | Score: {item.score ?? 'N/A'}
                                </span>
                              </div>
                              <div className="text-[10px] font-mono text-primary/90 bg-primary/5 px-1.5 py-0.5 rounded">
                                Formula: {item.formula}
                              </div>
                              <div className="text-[10px] text-text-muted">{item.explanation}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </motion.div>
              )
            })}

            {/* Typing / Loading Indicator */}
            {sendMutation.isPending && (
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-xl bg-gradient-primary flex items-center justify-center text-white shrink-0">
                  <LucideIcons.Bot className="h-4 w-4" />
                </div>
                <div className="clay-surface bg-card p-3 rounded-2xl border border-white/60 flex items-center gap-1.5">
                  <span
                    className="h-2 w-2 rounded-full bg-primary animate-bounce"
                    style={{ animationDelay: '0ms' }}
                  />
                  <span
                    className="h-2 w-2 rounded-full bg-primary animate-bounce"
                    style={{ animationDelay: '150ms' }}
                  />
                  <span
                    className="h-2 w-2 rounded-full bg-primary animate-bounce"
                    style={{ animationDelay: '300ms' }}
                  />
                </div>
              </div>
            )}

            {/* Error state */}
            {sendMutation.isError && (
              <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-danger/10 border border-danger/20 text-danger text-xs font-bold max-w-3xl mx-auto w-full">
                <LucideIcons.AlertCircle className="h-4 w-4 shrink-0" />
                <span>
                  {sendMutation.error?.message || 'Failed to send message. Please try again.'}
                </span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-border/80 bg-card/80 backdrop-blur-md shrink-0">
        <div className="max-w-3xl mx-auto flex flex-col gap-2">
          {/* Quick suggestions strip */}
          <div className="flex items-center gap-2 overflow-x-auto scrollbar-none pb-1">
            {advisorConfig.suggestedPrompts.slice(0, 3).map((p, idx) => (
              <button
                key={idx}
                onClick={() => setInputText(p.text)}
                className="text-[10px] font-bold px-2.5 py-1 rounded-lg bg-muted/40 border border-border/60 text-text-muted hover:text-text-primary hover:border-primary/20 shrink-0 cursor-pointer transition-colors"
              >
                + {p.text}
              </button>
            ))}
          </div>

          {/* Textarea Input Container */}
          <div className="relative clay-surface bg-card border border-border rounded-2xl p-2.5 shadow-sm focus-within:border-primary/40 transition-colors flex items-end gap-2">
            <textarea
              rows={2}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                conversationId
                  ? 'Continue the conversation...'
                  : 'Select or start a conversation first…'
              }
              disabled={!conversationId || sendMutation.isPending}
              className="w-full bg-transparent text-xs md:text-sm font-semibold text-text-primary placeholder:text-text-muted resize-none focus:outline-none px-2 py-1 scrollbar-none disabled:opacity-50"
            />

            {/* Input Actions Toolbar */}
            <div className="flex items-center gap-1.5 shrink-0">
              {inputText && (
                <button
                  onClick={() => setInputText('')}
                  className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-muted"
                  title="Clear text"
                >
                  <LucideIcons.X className="h-4 w-4" />
                </button>
              )}

              <button
                className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-muted cursor-not-allowed"
                title="Voice input (coming soon)"
              >
                <LucideIcons.Mic className="h-4 w-4" />
              </button>

              <Button
                variant="gradient"
                size="sm"
                onClick={handleSend}
                disabled={!inputText.trim() || !conversationId || sendMutation.isPending}
                className="rounded-xl px-3 py-2 font-black text-xs shadow-button"
                iconLeft={<LucideIcons.Send className="h-3.5 w-3.5" />}
              >
                Send
              </Button>
            </div>
          </div>

          {/* Footer hints */}
          <div className="flex justify-between items-center px-1 text-[9px] font-bold text-text-muted">
            <span>Press Shift + Enter for line break</span>
            <span>{inputText.length} chars</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatWorkspace
