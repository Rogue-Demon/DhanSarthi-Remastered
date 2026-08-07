import React, { useState } from 'react';
import { cn, helpers } from '@/utils';

export const Avatar = ({
  src,
  alt = '',
  name = '',
  size = 'md',
  online = null, // true, false, or null (hidden)
  circular = true,
  className,
  ...props
}) => {
  const [hasError, setHasError] = useState(false);

  const sizes = {
    xs: 'h-6 w-6 text-[10px]',
    sm: 'h-8 w-8 text-xs',
    md: 'h-10 w-10 text-sm',
    lg: 'h-12 w-12 text-base',
    xl: 'h-16 w-16 text-lg',
  };

  const statusSizes = {
    xs: 'h-1.5 w-1.5',
    sm: 'h-2 w-2',
    md: 'h-2.5 w-2.5',
    lg: 'h-3 w-3',
    xl: 'h-3.5 w-3.5',
  };

  const initials = helpers.getInitials(name);

  return (
    <div className="relative inline-block flex-shrink-0" {...props}>
      <div
        className={cn(
          'flex items-center justify-center overflow-hidden bg-muted border border-border text-text-secondary font-semibold select-none shadow-sm',
          circular ? 'rounded-full' : 'rounded-button',
          sizes[size] || sizes.md,
          className
        )}
      >
        {src && !hasError ? (
          <img
            src={src}
            alt={alt || name}
            onError={() => setHasError(true)}
            className="h-full w-full object-cover"
          />
        ) : (
          <span>{initials || '?'}</span>
        )}
      </div>
      {online !== null && (
        <span
          className={cn(
            'absolute bottom-0 right-0 block rounded-full border-2 border-card shadow-sm',
            online ? 'bg-success' : 'bg-text-muted',
            statusSizes[size] || statusSizes.md
          )}
        />
      )}
    </div>
  );
};

export default Avatar;
