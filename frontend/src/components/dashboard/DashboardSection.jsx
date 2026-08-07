import React from 'react';
import { cn } from '@/utils';
import { motion, useReducedMotion } from 'framer-motion';

/**
 * DashboardSection Component
 *
 * Wrapper to group widgets into logical sections.
 * Supports screen reader semantic accessibility.
 */
export function DashboardSection({
  title,
  subtitle,
  children,
  className,
  action,
  ...props
}) {
  const shouldReduceMotion = useReducedMotion();

  return (
    <motion.section
      initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className={cn('flex flex-col gap-4 w-full', className)}
      {...props}
    >
      {/* Section Header */}
      {(title || subtitle || action) && (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 px-1">
          <div className="flex flex-col">
            {title && (
              <h3 className="text-xl font-extrabold text-text-primary tracking-tight">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-xs font-bold text-text-muted mt-0.5">
                {subtitle}
              </p>
            )}
          </div>
          {action && <div className="self-start sm:self-center">{action}</div>}
        </div>
      )}

      {/* Section Body */}
      <div className="w-full">{children}</div>
    </motion.section>
  );
}

export default DashboardSection;
