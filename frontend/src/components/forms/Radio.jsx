import React, { forwardRef } from 'react';
import { cn } from '@/utils';

export const Radio = forwardRef(({
  className,
  checked,
  onChange,
  disabled = false,
  label,
  id,
  name,
  ...props
}, ref) => {
  return (
    <label className={cn('flex items-center gap-3 cursor-pointer select-none text-sm font-medium text-text-secondary', disabled && 'opacity-60 cursor-not-allowed')} htmlFor={id}>
      <input
        ref={ref}
        type="radio"
        id={id}
        name={name}
        checked={checked}
        onChange={onChange}
        disabled={disabled}
        className="sr-only"
        {...props}
      />
      <div
        className={cn(
          'h-5 w-5 rounded-full border border-border flex items-center justify-center transition-all duration-150 bg-card shadow-sm',
          checked && 'border-primary',
          disabled && 'bg-muted'
        )}
      >
        {checked && (
          <span className="h-2.5 w-2.5 rounded-full bg-primary animate-scaleIn" />
        )}
      </div>
      {label && <span>{label}</span>}
    </label>
  );
});

Radio.displayName = 'Radio';
export default Radio;
