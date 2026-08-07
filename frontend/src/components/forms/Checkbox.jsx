import React, { forwardRef } from 'react';
import { cn } from '@/utils';

export const Checkbox = forwardRef(({
  className,
  checked,
  onChange,
  disabled = false,
  label,
  id,
  ...props
}, ref) => {
  return (
    <label className={cn('flex items-center gap-3 cursor-pointer select-none text-sm font-medium text-text-secondary', disabled && 'opacity-60 cursor-not-allowed')} htmlFor={id}>
      <input
        ref={ref}
        type="checkbox"
        id={id}
        checked={checked}
        onChange={onChange}
        disabled={disabled}
        className="sr-only"
        {...props}
      />
      <div
        className={cn(
          'h-5 w-5 rounded border border-border flex items-center justify-center transition-all duration-150 bg-card shadow-sm',
          checked && 'bg-primary border-primary text-white shadow-button',
          disabled && 'bg-muted'
        )}
      >
        {checked && (
          <svg className="h-3.5 w-3.5 stroke-[3]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        )}
      </div>
      {label && <span>{label}</span>}
    </label>
  );
});

Checkbox.displayName = 'Checkbox';
export default Checkbox;
