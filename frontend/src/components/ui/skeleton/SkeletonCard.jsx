import React from 'react';
import Skeleton from './Skeleton';
import SkeletonText from './SkeletonText';
import SkeletonAvatar from './SkeletonAvatar';

/**
 * Skeleton for a card component.
 * Renders a placeholder for card header (avatar + title) and content lines.
 */
export default function SkeletonCard({
  avatarSize = '2.5rem',
  titleWidth = '60%',
  lineCount = 3,
  lineWidth = '100%',
  className = '',
}) {
  const lines = Array.from({ length: lineCount });
  return (
    <div className={`p-4 rounded-lg bg-surface shadow-sm ${className}`}> // assume bg-surface token
      <div className="flex items-center mb-4">
        <SkeletonAvatar size={avatarSize} className="mr-3" />
        <SkeletonText width={titleWidth} height="1rem" />
      </div>
      {lines.map((_, i) => (
        <SkeletonText
          key={i}
          width={lineWidth}
          height="0.875rem"
          className="mb-2"
        />
      ))}
    </div>
  );
}
