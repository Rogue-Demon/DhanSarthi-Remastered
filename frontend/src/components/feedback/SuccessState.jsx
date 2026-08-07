import React from 'react';
import EmptyState from './EmptyState';

export const SuccessState = ({
  title = 'Success!',
  description = 'Your operation has been completed successfully.',
  onConfirm,
  confirmText = 'Continue',
  ...props
}) => {
  const successIllustration = (
    <div className="rounded-2xl bg-success/10 p-4 text-success flex items-center justify-center">
      <svg className="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    </div>
  );

  return (
    <EmptyState
      title={title}
      description={description}
      illustration={successIllustration}
      actionText={onConfirm ? confirmText : undefined}
      onAction={onConfirm}
      {...props}
    />
  );
};

export default SuccessState;
