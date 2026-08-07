import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/utils';

export const Switch = ({
  checked,
  onChange,
  disabled = false,
  label,
  id,
  ...props
}) => {
  return (
    <label
      className={cn(
        'flex items-center gap-3 cursor-pointer select-none text-sm font-medium text-text-secondary',
        disabled && 'opacity-60 cursor-not-allowed'
      )}
      htmlFor={id}
    >
      <input
        type="checkbox"
        id={id}
        checked={checked}
        onChange={disabled ? undefined : onChange}
        disabled={disabled}
        className="sr-only"
        {...props}
      />
      <div
        className={cn(
          'w-11 h-6 bg-border rounded-full p-0.5 transition-colors duration-200 ease-in-out relative flex items-center',
          checked && 'bg-primary'
        )}
      >
        <motion.div
          className="bg-card w-5 h-5 rounded-full shadow-sm"
          layout
          animate={{ x: checked ? 20 : 0 }}
          transition={{ type: 'spring', stiffness: 500, damping: 30 }}
        />
      </div>
      {label && <span>{label}</span>}
    </label>
  );
};

export default Switch;
