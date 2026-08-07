import React, { forwardRef } from 'react';
import { cn } from '@/utils';

export const Input = forwardRef(({
  className,
  type = 'text',
  error = false,
  success = false,
  disabled = false,
  readOnly = false,
  iconLeft,
  iconRight,
  prefixText,
  suffixText,
  onClear,
  value,
  id,
  ...props
}, ref) => {
  return (
    <div className="relative w-full flex items-center">
      {prefixText && (
        <span className="absolute left-4 text-sm font-semibold text-text-secondary select-none">
          {prefixText}
        </span>
      )}
      {iconLeft && (
        <span className="absolute left-4 text-text-muted flex items-center justify-center pointer-events-none">
          {iconLeft}
        </span>
      )}
      <input
        ref={ref}
        type={type}
        id={id}
        value={value}
        disabled={disabled}
        readOnly={readOnly}
        className={cn(
          'w-full bg-card border border-border text-text-primary px-4 py-3 rounded-input text-base transition-all duration-200 outline-none shadow-sm focus:ring-2 focus:ring-primary/40 focus:border-primary',
          prefixText && 'pl-10',
          iconLeft && !prefixText && 'pl-11',
          suffixText && 'pr-10',
          iconRight && !suffixText && 'pr-11',
          onClear && value && 'pr-10',
          error && 'border-destructive focus:ring-destructive/30 focus:border-destructive',
          success && 'border-success focus:ring-success/30 focus:border-success',
          disabled && 'opacity-60 bg-muted cursor-not-allowed pointer-events-none',
          readOnly && 'bg-muted cursor-default',
          className
        )}
        {...props}
      />
      {onClear && value && !disabled && !readOnly && (
        <button
          type="button"
          onClick={onClear}
          className="absolute right-4 rounded-full p-0.5 hover:bg-black/10 dark:hover:bg-white/10 outline-none text-text-muted cursor-pointer"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
      {!onClear && suffixText && (
        <span className="absolute right-4 text-sm font-semibold text-text-secondary select-none">
          {suffixText}
        </span>
      )}
      {!onClear && !suffixText && iconRight && (
        <span className="absolute right-4 text-text-muted flex items-center justify-center pointer-events-none">
          {iconRight}
        </span>
      )}
    </div>
  );
});

Input.displayName = 'Input';
export default Input;
