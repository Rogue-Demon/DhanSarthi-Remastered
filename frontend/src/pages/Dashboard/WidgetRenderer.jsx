import React from 'react';
import { WidgetRenderer as BaseRenderer } from '@/components/dashboard';

/**
 * WidgetRenderer Component (Page wrapper)
 * Dynamically resolves widgets from registry.
 */
export function WidgetRenderer(props) {
  return <BaseRenderer {...props} />;
}

export default WidgetRenderer;
