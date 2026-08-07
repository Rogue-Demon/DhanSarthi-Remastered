import React from 'react';
import Skeleton from './Skeleton';

/**
 * Skeleton for a single line of text.
 * Props: width (default 100%), height (default 1rem), className.
 */
export default function SkeletonText({ width = '100%', height = '1rem', className = '' }) {
  return <Skeleton width={width} height={height} className={className} />;
}
