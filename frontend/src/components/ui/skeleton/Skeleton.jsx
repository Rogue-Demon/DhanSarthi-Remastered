import React from 'react';
import './Skeleton.css';
import { useReducedMotion } from 'framer-motion';

/**
 * Base Skeleton component.
 * Props:
 * - width, height (e.g., '100%', '2rem')
 * - className for additional styling
 * - style for inline styles
 */
export default function Skeleton({ width = '100%', height = '1rem', className = '', style = {} }) {
  const reduceMotion = useReducedMotion();
  const skeletonStyle = {
    width,
    height,
    ...style,
  };
  return (
    <div
      className={`skeleton-base ${className} ${reduceMotion ? 'skeleton-reduced' : ''}`}
      style={skeletonStyle}
    />
  );
}
