import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/utils';

export const Chip = ({
  children,
  className,
  type = 'selectable', // selectable, filter, status
  active = false,
  status = 'neutral', // success, warning, danger, neutral
  onToggle,
  onRemove,
  disabled = false,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-medium rounded-full select-none cursor-pointer border transition-all duration-150';

  const typeStyles = {
    selectable: active
      ? 'bg-primary text-white border-primary shadow-sm'
      : 'bg-card text-text-primary border-border hover:bg-muted',
    filter: active
      ? 'bg-primary/10 text-primary border-primary/20 hover:bg-primary/20'
      : 'bg-card text-text-secondary border-border hover:bg-muted',
    status: {
      neutral: 'bg-muted text-text-secondary border-border cursor-default',
      success: 'bg-success/10 text-success border-success/20 cursor-default',
      warning: 'bg-warning/10 text-warning border-warning/20 cursor-default',
      danger: 'bg-destructive/10 text-destructive border-destructive/20 cursor-default',
    }[status],
  };

  const currentStyles = type === 'status' ? typeStyles.status : typeStyles[type];

  return (
    <motion.div
      className={cn(
        baseStyles,
        'px-3 py-1 text-sm gap-1.5',
        currentStyles,
        disabled && 'opacity-50 pointer-events-none cursor-not-allowed',
        className
      )}
      onClick={!disabled && type !== 'status' ? onToggle : undefined}
      whileHover={(!disabled && type !== 'status') ? { scale: 1.03 } : {}}
      whileTap={(!disabled && type !== 'status') ? { scale: 0.97 } : {}}
      {...props}
    >
      {type === 'status' && (
        <span
          className={cn(
            'h-2 w-2 rounded-full',
            {
              neutral: 'bg-text-secondary',
              success: 'bg-success',
              warning: 'bg-warning',
              danger: 'bg-destructive',
            }[status]
          )}
        />
      )}
      <span>{children}</span>
      {type === 'filter' && onRemove && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            if (!disabled) onRemove();
          }}
          className="ml-1 rounded-full p-0.5 hover:bg-black/10 dark:hover:bg-white/10 outline-none"
        >
          <svg className="h-3 w-3 text-current" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </motion.div>
  );
};

export default Chip;
