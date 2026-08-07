import React, { forwardRef } from 'react';
import Button from './Button';

export const IconButton = forwardRef(({
  icon,
  className,
  variant = 'secondary',
  size = 'md',
  circular = true,
  ariaLabel,
  tooltip,
  ...props
}, ref) => {
  return (
    <Button
      ref={ref}
      variant={variant}
      size={size}
      circular={circular}
      className={className}
      aria-label={ariaLabel}
      title={tooltip}
      {...props}
    >
      {icon}
    </Button>
  );
});

IconButton.displayName = 'IconButton';
export default IconButton;
