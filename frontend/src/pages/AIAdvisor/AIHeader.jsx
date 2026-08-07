import React from 'react';
import { useProfile } from '@/hooks';
import { Badge, Button } from '@/components/ui';
import * as LucideIcons from 'lucide-react';
import { cn } from '@/utils';

/**
 * AIHeader Component
 * Title bar for the AI Advisor workspace with model selector, actions, and drawer toggle.
 */
export function AIHeader({ onOpenSidebar, className, ...props }) {
  const { profile, profileConfig } = useProfile();

  return (
    <div
      className={cn(
        'flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 border-b border-border/80 bg-card/80 backdrop-blur-md select-none shrink-0',
        className
      )}
      {...props}
    >
      {/* Title & Mobile Drawer Toggle */}
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenSidebar}
          className="p-2 rounded-xl border border-border bg-card text-text-muted hover:text-text-primary md:hidden"
          aria-label="Open sidebar"
        >
          <LucideIcons.Menu className="h-4 w-4" />
        </button>

        <div className="flex items-center gap-2.5">
          <div className="h-9 w-9 rounded-xl bg-gradient-primary flex items-center justify-center text-white shadow-xs">
            <LucideIcons.Bot className="h-5 w-5" />
          </div>
          <div className="flex flex-col text-left">
            <div className="flex items-center gap-2">
              <h2 className="text-base font-black text-text-primary tracking-tight">
                AI Advisor
              </h2>
              {profileConfig && (
                <Badge
                  variant="secondary"
                  className="text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded-md border"
                  style={{
                    color: profileConfig.color,
                    borderColor: `${profileConfig.color}25`,
                    background: `${profileConfig.color}10`,
                  }}
                >
                  {profileConfig.label}
                </Badge>
              )}
            </div>
            <span className="text-[10px] font-bold text-text-muted flex items-center gap-1">
              <span className="h-1.5 w-1.5 rounded-full bg-success animate-pulse" />
              DhanSarthi Finance LLM v2.4
            </span>
          </div>
        </div>
      </div>

      {/* Model Selector & Quick Toolbar */}
      <div className="flex items-center gap-2.5 self-end sm:self-center">
        {/* Model Dropdown Placeholder */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-border bg-card text-xs font-bold text-text-secondary cursor-not-allowed">
          <LucideIcons.Sparkles className="h-3.5 w-3.5 text-accent" />
          <span className="hidden sm:inline">Model:</span>
          <span className="text-text-primary font-black">Financial-GPT</span>
          <LucideIcons.ChevronDown className="h-3.5 w-3.5 text-text-muted ml-0.5" />
        </div>

        {/* Export Chat */}
        <Button
          variant="ghost"
          size="sm"
          className="rounded-xl p-2 border border-border text-text-muted hover:text-text-primary"
          onClick={() => console.log('Export conversation')}
          title="Export Conversation"
        >
          <LucideIcons.Download className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

export default AIHeader;
