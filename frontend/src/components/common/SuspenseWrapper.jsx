import React, { Suspense } from 'react';
import Loading from './Loading';
import ErrorBoundary from './ErrorBoundary';

export default function SuspenseWrapper({ children, fallback, errorFallback }) {
  return (
    <ErrorBoundary fallback={errorFallback}>
      <Suspense fallback={fallback || <Loading className="min-h-[200px]" />}>
        {children}
      </Suspense>
    </ErrorBoundary>
  );
}
