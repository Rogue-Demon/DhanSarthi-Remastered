import React from 'react';
import { Link } from 'react-router-dom';
import { cn } from '@/utils';

export const Breadcrumb = ({
  items = [], // Array of { label, path }
  className,
  ...props
}) => {
  return (
    <nav aria-label="Breadcrumb" className={cn('text-sm select-none', className)} {...props}>
      <ol className="flex items-center gap-2 text-text-secondary font-medium">
        {items.map((item, index) => {
          const isLast = index === items.length - 1;

          return (
            <li key={index} className="flex items-center gap-2">
              {index > 0 && (
                <span className="text-text-muted select-none">/</span>
              )}
              {isLast ? (
                <span className="text-text-primary font-semibold">{item.label}</span>
              ) : (
                <Link
                  to={item.path}
                  className="hover:text-text-primary transition-colors duration-150"
                >
                  {item.label}
                </Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
};

export default Breadcrumb;
