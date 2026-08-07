import React from 'react';
import Alert from './Alert';
import { cn } from '@/utils';

export const Toast = ({
  message,
  type = 'info',
  onClose,
  className,
  ...props
}) => {
  return (
    <div
      className={cn(
        'fixed bottom-6 right-6 w-full max-w-sm z-50 animate-slideUp shadow-lg rounded-xl overflow-hidden',
        className
      )}
      {...props}
    >
      <Alert
        variant={type}
        description={message}
        onClose={onClose}
        className="bg-card border-border shadow-md"
      />
    </div>
  );
};

export default Toast;
