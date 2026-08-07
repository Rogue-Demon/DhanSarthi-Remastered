import React from 'react';
import { DashboardGrid as BaseGrid } from '@/components/dashboard';

/**
 * DashboardGrid Component (Page wrapper)
 * Coordinates sizing spans and responsive behaviors.
 */
export function DashboardGrid({ children, ...props }) {
  return <BaseGrid {...props}>{children}</BaseGrid>;
}

export default DashboardGrid;
