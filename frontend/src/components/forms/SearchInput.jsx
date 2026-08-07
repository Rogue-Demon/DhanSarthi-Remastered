import React, { forwardRef } from 'react';
import Input from './Input';

export const SearchInput = forwardRef(({ className, ...props }, ref) => {
  const searchIcon = (
    <svg className="h-5 w-5 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
    </svg>
  );

  return (
    <Input
      ref={ref}
      iconLeft={searchIcon}
      className={className}
      {...props}
    />
  );
});

SearchInput.displayName = 'SearchInput';
export default SearchInput;
