import React from 'react';
import { cn } from '@/utils';

export const Section = ({
  children,
  className,
  ...props
}) => {
  return (
    <section
      className={cn('section-container', className)}
      {...props}
    >
      {children}
    </section>
  );
};

export default Section;
