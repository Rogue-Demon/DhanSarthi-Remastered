import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { cn } from '@/utils';
import * as LucideIcons from 'lucide-react';

/**
 * WidgetContainer Component
 *
 * Core layout wrapper for all widgets.
 * Standardizes:
 * - Claymorphic appearance
 * - Custom state handling (Loading, Empty, Error)
 * - Custom layout headers, titles, actions
 * - Entrance and interaction micro-animations
 */
export function WidgetContainer({
  title,
  icon,
  color,
  toolbar,
  loading = false,
  error = false,
  empty = false,
  errorMessage = 'Failed to load widget data.',
  emptyMessage = 'No data available.',
  interactive = false,
  className,
  children,
  sizeClass = '', // specific grid col spans (e.g. col-span-4)
  ...props
}) {
  const shouldReduceMotion = useReducedMotion();

  // Entrance variants
  const entryVariants = {
    hidden: { opacity: 0, y: shouldReduceMotion ? 0 : 15 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        type: 'spring',
        stiffness: 300,
        damping: 24,
      },
    },
  };

  return (
    <motion.div
      variants={entryVariants}
      className={cn(
        // Base claymorphism styles
        'clay-surface flex flex-col justify-between h-full min-h-[220px]',
        interactive ? 'clay-surface-interactive cursor-pointer' : '',
        sizeClass,
        className
      )}
      {...props}
    >
      {/* Widget Header */}
      {(title || icon || toolbar) && (
        <div className="flex items-center justify-between border-b border-border/60 pb-3 p-5 select-none shrink-0 bg-surface/30">
          <div className="flex items-center gap-3">
            {icon && (
              <div
                className="p-2 rounded-xl flex items-center justify-center border border-white/20 dark:border-white/5 shadow-xs"
                style={{
                  background: color ? `${color}12` : 'var(--muted)',
                  color: color || 'var(--text-secondary)',
                }}
              >
                {React.createElement(LucideIcons[icon] || LucideIcons.HelpCircle, {
                  className: 'h-4.5 w-4.5 stroke-[2.2]',
                })}
              </div>
            )}
            <span className="text-sm font-extrabold text-text-primary tracking-tight">
              {title}
            </span>
          </div>
          {toolbar && <div className="flex items-center gap-1.5">{toolbar}</div>}
        </div>
      )}

      {/* Widget Content Area */}
      <div className="flex-1 p-5 flex flex-col justify-center relative overflow-hidden bg-card/45">
        {loading && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-card/60 backdrop-blur-xs gap-3">
            <div className="h-9 w-9 rounded-full border-3 border-primary/20 border-t-primary animate-spin" />
            <span className="text-xs font-bold text-text-muted">Loading widget...</span>
          </div>
        )}

        {error && !loading && (
          <div className="flex flex-col items-center justify-center text-center p-4 gap-2.5">
            <div className="p-3 rounded-full bg-danger/10 text-danger border border-danger/15 shadow-xs">
              <LucideIcons.AlertTriangle className="h-5 w-5" />
            </div>
            <p className="text-xs font-black text-text-primary">System Alert</p>
            <p className="text-xs font-bold text-text-muted max-w-[200px] leading-normal">
              {errorMessage}
            </p>
          </div>
        )}

        {empty && !loading && !error && (
          <div className="flex flex-col items-center justify-center text-center p-4 gap-2.5">
            <div className="p-3 rounded-full bg-muted text-text-muted border border-border shadow-xs">
              <LucideIcons.Inbox className="h-5 w-5" />
            </div>
            <p className="text-xs font-black text-text-primary">No Activity</p>
            <p className="text-xs font-bold text-text-muted max-w-[200px] leading-normal">
              {emptyMessage}
            </p>
          </div>
        )}

        {!loading && !error && !empty && children}
      </div>
    </motion.div>
  );
}

export default WidgetContainer;
