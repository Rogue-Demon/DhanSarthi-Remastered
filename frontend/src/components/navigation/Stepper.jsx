import React from 'react';
import { cn } from '@/utils';

export const Stepper = ({
  steps = [], // Array of string titles or { label, description }
  currentStep = 0, // 0-indexed
  className,
  ...props
}) => {
  return (
    <div className={cn('flex items-center w-full select-none justify-between gap-4', className)} {...props}>
      {steps.map((step, index) => {
        const isCompleted = index < currentStep;
        const isActive = index === currentStep;
        const isLast = index === steps.length - 1;
        const stepLabel = typeof step === 'string' ? step : step.label;

        return (
          <React.Fragment key={index}>
            <div className="flex items-center gap-2.5">
              <span
                className={cn(
                  'h-8 w-8 rounded-full flex items-center justify-center font-bold text-sm border-2 transition-all duration-200',
                  isCompleted && 'bg-primary border-primary text-white',
                  isActive && 'border-primary text-primary bg-primary/5',
                  !isCompleted && !isActive && 'border-border text-text-muted bg-card'
                )}
              >
                {isCompleted ? (
                  <svg className="h-4 w-4 stroke-[3]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  index + 1
                )}
              </span>
              <span
                className={cn(
                  'text-sm font-semibold',
                  isActive ? 'text-primary' : 'text-text-secondary'
                )}
              >
                {stepLabel}
              </span>
            </div>
            {!isLast && (
              <div
                className={cn(
                  'flex-1 h-0.5 min-w-[20px] transition-colors duration-200',
                  isCompleted ? 'bg-primary' : 'bg-border'
                )}
              />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};

export default Stepper;
