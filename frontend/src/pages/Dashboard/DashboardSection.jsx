import React from 'react';
import { DashboardSection as BaseSection } from '@/components/dashboard';

/**
 * DashboardSection Component (Page wrapper)
 * Logical grouping card container layout.
 */
export function DashboardSection({ children, ...props }) {
  return <BaseSection {...props}>{children}</BaseSection>;
}

export default DashboardSection;
