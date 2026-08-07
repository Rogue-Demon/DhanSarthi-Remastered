import React from 'react';
import { cn } from '@/utils';

export const Slider = ({
  min = 0,
  max = 100,
  step = 1,
  value,
  onChange,
  disabled = false,
  className,
  id,
  ...props
}) => {
  return (
    <input
      type="range"
      id={id}
      min={min}
      max={max}
      step={step}
      value={value}
      onChange={onChange}
      disabled={disabled}
      className={cn(
        'w-full h-2 bg-border rounded-lg appearance-none cursor-pointer accent-primary focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed',
        className
      )}
      {...props}
    />
  );
};

export default Slider;
