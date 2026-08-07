import React, { useState, useRef, useEffect } from 'react';
import { useProfile } from '@/hooks';
import { getAIAdvisorConfig, placeholderMessages } from '@/config';
import { motion, useReducedMotion } from 'framer-motion';
import { Badge, Button } from '@/components/ui';
import * as LucideIcons from 'lucide-react';
import { cn } from '@/utils';

/**
 * ChatWorkspace Component
 *
 * Full-featured interactive chat interface containing:
 * - Welcome screen hero with profile-customized prompts
 * - Chat message thread with copy/like/bookmark actions
 * - Auto-scrolling scroll container
 * - Auto-growing input textarea with voice/attachment/clear tools
 */
export function ChatWorkspace({ initialPrompt = '' }) {
  const { profile } = useProfile();
  const shouldReduceMotion = useReducedMotion();
  const advisorConfig = getAIAdvisorConfig(profile);

  const [messages, setMessages] = useState(placeholderMessages);
  const [inputText, setInputText] = useState(initialPrompt);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (initialPrompt) {
      setInputText(initialPrompt);
    }
  }, [initialPrompt]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSend = () => {
    if (!inputText.trim()) return;

    const userMsg = {
      id: `u-${Date.now()}`,
      role: 'user',
      content: inputText.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setIsTyping(true);

    // Simulate AI typing response (static placeholder response)
    setTimeout(() => {
      setIsTyping(false);
      const assistantMsg = {
        id: `a-${Date.now()}`,
        role: 'assistant',
        content: "I've analyzed your financial query based on your active profile parameters. Here is the recommended breakdown:\n\n• Maintain a 20% liquid cash allocation.\n• Review recurring subscriptions for potential savings.\n• Keep 6 months of expenses in an emergency fund.\n\n*(Note: This is a static UI workspace placeholder ready for backend LLM integration.)*",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    }, 1500);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handlePromptClick = (promptText) => {
    setInputText(promptText);
  };

  return (
    <div className="flex flex-col h-full w-full bg-background overflow-hidden relative select-none">
      
      {/* Scrollable Chat Area */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 scrollbar-none">
        
        {/* Welcome Screen (if empty) */}
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center min-h-[70%] text-center max-w-2xl mx-auto gap-6 my-auto py-10">
            <div className="h-16 w-16 rounded-3xl bg-gradient-primary flex items-center justify-center text-white shadow-floating">
              <LucideIcons.Sparkles className="h-8 w-8 animate-pulse" />
            </div>

            <div className="flex flex-col gap-2">
              <Badge variant="secondary" className="mx-auto text-[10px] font-black uppercase tracking-widest bg-primary/10 text-primary border-primary/20 py-0.5 px-3 rounded-full">
                AI Financial Workspace
              </Badge>
              <h3 className="text-2xl md:text-3xl font-black text-text-primary tracking-tight">
                {advisorConfig.welcome.greeting}
              </h3>
              <p className="text-xs md:text-sm font-semibold text-text-muted leading-relaxed max-w-lg">
                {advisorConfig.welcome.description}
              </p>
            </div>

            {/* Suggested Prompt Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 w-full pt-4">
              {advisorConfig.suggestedPrompts.map((prompt, idx) => {
                const Icon = LucideIcons[prompt.icon] || LucideIcons.HelpCircle;

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
                      <span className="text-[9px] font-black text-text-muted uppercase tracking-wider">{prompt.category}</span>
                      <span className="text-xs font-bold text-text-primary group-hover:text-primary transition-colors">{prompt.text}</span>
                    </div>
                  </motion.button>
                );
              })}
            </div>
          </div>
        ) : (
          /* Messages List */
          <div className="flex flex-col gap-5 max-w-3xl mx-auto w-full">
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={cn('flex items-start gap-3 w-full', msg.role === 'user' ? 'flex-row-reverse' : 'flex-row')}
              >
                {/* Avatar */}
                <div
                  className={cn(
                    'h-8 w-8 rounded-xl flex items-center justify-center shrink-0 text-white font-black text-xs shadow-xs',
                    msg.role === 'user' ? 'bg-accent' : 'bg-gradient-primary'
                  )}
                >
                  {msg.role === 'user' ? <LucideIcons.User className="h-4 w-4" /> : <LucideIcons.Bot className="h-4 w-4" />}
                </div>

                {/* Message Bubble & Content */}
                <div className={cn('flex flex-col gap-1.5 max-w-[85%] text-left', msg.role === 'user' ? 'items-end' : 'items-start')}>
                  <div className="flex items-center gap-2 px-1">
                    <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                      {msg.role === 'user' ? 'You' : 'DhanSarthi AI'}
                    </span>
                    <span className="text-[9px] font-bold text-text-muted">{msg.timestamp}</span>
                  </div>

                  <div
                    className={cn(
                      'p-4 rounded-2xl text-xs md:text-sm font-medium leading-relaxed shadow-xs whitespace-pre-wrap',
                      msg.role === 'user'
                        ? 'bg-primary text-white rounded-tr-none'
                        : 'clay-surface bg-card border border-white/60 dark:border-white/5 text-text-primary rounded-tl-none'
                    )}
                  >
                    {msg.content}
                  </div>

                  {/* Message Action Toolbar (for Assistant responses) */}
                  {msg.role === 'assistant' && (
                    <div className="flex items-center gap-1 pt-1 text-text-muted">
                      <button className="p-1 rounded hover:bg-muted text-text-muted hover:text-text-primary" title="Copy text">
                        <LucideIcons.Copy className="h-3.5 w-3.5" />
                      </button>
                      <button className="p-1 rounded hover:bg-muted text-text-muted hover:text-success" title="Like response">
                        <LucideIcons.ThumbsUp className="h-3.5 w-3.5" />
                      </button>
                      <button className="p-1 rounded hover:bg-muted text-text-muted hover:text-danger" title="Dislike response">
                        <LucideIcons.ThumbsDown className="h-3.5 w-3.5" />
                      </button>
                      <button className="p-1 rounded hover:bg-muted text-text-muted hover:text-accent" title="Bookmark">
                        <LucideIcons.Bookmark className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  )}
                </div>
              </motion.div>
            ))}

            {/* Typing Indicator */}
            {isTyping && (
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-xl bg-gradient-primary flex items-center justify-center text-white shrink-0">
                  <LucideIcons.Bot className="h-4 w-4" />
                </div>
                <div className="clay-surface bg-card p-3 rounded-2xl border border-white/60 flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="h-2 w-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="h-2 w-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
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
              placeholder="Ask DhanSarthi AI anything about your finances..."
              className="w-full bg-transparent text-xs md:text-sm font-semibold text-text-primary placeholder:text-text-muted resize-none focus:outline-none px-2 py-1 scrollbar-none"
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

              <button className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-muted cursor-not-allowed" title="Voice input placeholder">
                <LucideIcons.Mic className="h-4 w-4" />
              </button>

              <button className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-muted cursor-not-allowed" title="Attachment placeholder">
                <LucideIcons.Paperclip className="h-4 w-4" />
              </button>

              <Button
                variant="gradient"
                size="sm"
                onClick={handleSend}
                disabled={!inputText.trim()}
                className="rounded-xl px-3 py-2 font-black text-xs shadow-button"
                iconLeft={<LucideIcons.Send className="h-3.5 w-3.5" />}
              >
                Send
              </Button>
            </div>
          </div>

          {/* Keyboard Hint */}
          <div className="flex justify-between items-center px-1 text-[9px] font-bold text-text-muted">
            <span>Press Shift + Enter for line break</span>
            <span>{inputText.length} chars</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ChatWorkspace;
