import React from 'react';
import { EmptyDashboard as BaseEmpty } from '@/components/dashboard';

/**
 * EmptyDashboard Component (Page wrapper)
 * Renders fallback dashboard view.
 */
export function EmptyDashboard(props) {
  return <BaseEmpty {...props} />;
}

export default EmptyDashboard;
