import React from 'react';
import Skeleton from './Skeleton';

/**
 * Skeleton for avatar/profile picture.
 * Props: size (default '2rem'), className.
 */
export default function SkeletonAvatar({ size = '2rem', className = '' }) {
  return (
    <Skeleton
      width={size}
      height={size}
      className={`rounded-full ${className}`}
    />
  );
}
