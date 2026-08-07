import React from 'react';
import SuspenseWrapper from '@/components/common/SuspenseWrapper';

export function LazyLoader({ component: Component, ...props }) {
  return (
    <SuspenseWrapper>
      <Component {...props} />
    </SuspenseWrapper>
  );
}

export default LazyLoader;
