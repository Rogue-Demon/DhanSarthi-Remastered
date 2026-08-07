import React from 'react';
import Skeleton from './Skeleton';

/**
 * Skeleton for a button element.
 * Props: width (default '100%'), height (default '2.5rem'), className.
 */
export default function SkeletonButton({ width = '100%', height = '2.5rem', className = '' }) {
  return <Skeleton width={width} height={height} className={`rounded ${className}`} />;
}
