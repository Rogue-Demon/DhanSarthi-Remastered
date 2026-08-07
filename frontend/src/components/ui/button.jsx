import React, { forwardRef } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/utils';

export const Button = forwardRef(({
  children,
  className,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  iconLeft,
  iconRight,
  fullWidth = false,
  rounded = true,
  circular = false,
  onClick,
  type = 'button',
  ...props
}, ref) => {
  const baseStyles = 'inline-flex items-center justify-center font-semibold transition-all duration-200 outline-none focus:ring-2 focus:ring-primary/40 active:scale-[0.98] select-none cursor-pointer';

  const variants = {
    primary: 'bg-primary text-white hover:bg-primary-hover shadow-button',
    secondary: 'bg-card text-text-primary hover:bg-muted border border-border shadow-sm',
    outline: 'bg-transparent border-2 border-primary text-primary hover:bg-primary/5',
    ghost: 'bg-transparent text-text-primary hover:bg-muted',
    gradient: 'bg-gradient-primary text-white hover:opacity-95 shadow-button',
    destructive: 'bg-destructive text-white hover:bg-destructive/90 shadow-sm',
    success: 'bg-success text-white hover:bg-success/90 shadow-sm',
  };

  const sizes = {
    xs: 'px-2.5 py-1.5 text-xs gap-1',
    sm: 'px-3.5 py-2 text-sm gap-1.5',
    md: 'px-5 py-2.5 text-base gap-2',
    lg: 'px-6 py-3 text-lg gap-2',
    xl: 'px-8 py-4 text-xl gap-2.5',
  };

  const buttonClasses = cn(
    baseStyles,
    variants[variant],
    sizes[size],
    fullWidth && 'w-full',
    circular ? 'rounded-full aspect-square p-2' : rounded ? 'rounded-button' : 'rounded-none',
    (disabled || loading) && 'opacity-60 cursor-not-allowed pointer-events-none active:scale-100',
    className
  );

  return (
    <motion.button
      ref={ref}
      type={type}
      disabled={disabled || loading}
      onClick={onClick}
      className={buttonClasses}
      whileHover={(!disabled && !loading) ? { y: -2, scale: 1.02 } : {}}
      whileTap={(!disabled && !loading) ? { scale: 0.98 } : {}}
      {...props}
    >
      {loading && (
        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-current" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
      )}
      {!loading && iconLeft && <span className="flex-shrink-0">{iconLeft}</span>}
      {children}
      {!loading && iconRight && <span className="flex-shrink-0">{iconRight}</span>}
    </motion.button>
  );
});

Button.displayName = 'Button';
export default Button;
