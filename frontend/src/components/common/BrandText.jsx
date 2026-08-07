import React from 'react';
import { cn } from '@/utils';
import GradientText from '@/components/display/GradientText';

export function BrandText({ className, size = 'md', ...props }) {
  const sizes = {
    sm: 'text-sm font-bold',
    md: 'text-base font-bold',
    lg: 'text-xl font-bold tracking-tight',
  };

  return (
    <GradientText
      variant="primary"
      className={cn(sizes[size] || sizes.md, 'font-extrabold', className)}
      {...props}
    >
      धनSarthi
    </GradientText>
  );
}

export default BrandText;
