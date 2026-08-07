import React from 'react';
import { cn } from '@/utils';
import Button from '@/components/ui/Button';

export const Pagination = ({
  currentPage = 1,
  totalPages = 1,
  onPageChange,
  className,
  ...props
}) => {
  const getPages = () => {
    const pages = [];
    for (let i = 1; i <= totalPages; i++) {
      pages.push(i);
    }
    return pages;
  };

  return (
    <nav aria-label="Pagination" className={cn('flex items-center gap-2 justify-center py-2 select-none', className)} {...props}>
      <Button
        variant="secondary"
        size="sm"
        disabled={currentPage <= 1}
        onClick={() => onPageChange(currentPage - 1)}
      >
        Previous
      </Button>

      {getPages().map((page) => (
        <Button
          key={page}
          variant={page === currentPage ? 'primary' : 'secondary'}
          size="sm"
          onClick={() => onPageChange(page)}
          className="h-9 w-9 p-0"
        >
          {page}
        </Button>
      ))}

      <Button
        variant="secondary"
        size="sm"
        disabled={currentPage >= totalPages}
        onClick={() => onPageChange(currentPage + 1)}
      >
        Next
      </Button>
    </nav>
  );
};

export default Pagination;
