import React from 'react';
import { DashboardHeader as BaseHeader } from '@/components/dashboard';

/**
 * DashboardHeader Component (Page wrapper)
 * Standard user greeting header layout.
 */
export function DashboardHeader(props) {
  return <BaseHeader {...props} />;
}

export default DashboardHeader;
