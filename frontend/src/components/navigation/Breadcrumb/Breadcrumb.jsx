import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { cn } from '@/utils';

export function Breadcrumb({ className, ...props }) {
  const location = useLocation();
  const pathnames = location.pathname.split('/').filter((x) => x);

  const getBreadcrumbItems = () => {
    const items = [{ label: 'Home', path: '/' }];
    let currentPath = '';

    pathnames.forEach((segment) => {
      currentPath += `/${segment}`;
      const label = segment
        .split('-')
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
      items.push({ label, path: currentPath });
    });

    return items;
  };

  const items = getBreadcrumbItems();

  return (
    <nav aria-label="Breadcrumb" className={cn('text-sm select-none hidden sm:block', className)} {...props}>
      <ol className="flex items-center gap-2 text-text-secondary font-medium">
        {items.map((item, index) => {
          const isLast = index === items.length - 1;

          return (
            <li key={index} className="flex items-center gap-2">
              {index > 0 && (
                <span className="text-text-muted select-none">/</span>
              )}
              {isLast ? (
                <span className="text-text-primary font-semibold truncate max-w-[120px]">{item.label}</span>
              ) : (
                <Link
                  to={item.path}
                  className="hover:text-text-primary transition-colors duration-150 truncate max-w-[100px]"
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
}

export default Breadcrumb;
