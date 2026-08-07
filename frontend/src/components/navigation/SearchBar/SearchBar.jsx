import React, { useState, useRef } from 'react';
import { cn } from '@/utils';

export function SearchBar({ className, ...props }) {
  const [value, setValue] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef(null);

  const handleClear = () => {
    setValue('');
    inputRef.current?.focus();
  };

  return (
    <div
      className={cn(
        'relative flex items-center bg-muted/40 border border-border rounded-xl px-3 py-1.5 transition-all duration-200 w-full max-w-[280px] md:max-w-[360px]',
        isFocused && 'border-primary ring-2 ring-primary/10 shadow-sm scale-[1.01]',
        className
      )}
      {...props}
    >
      <svg className="h-4.5 w-4.5 text-text-muted mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        placeholder="Quick search..."
        className="w-full bg-transparent text-sm text-text-primary placeholder-text-muted outline-none border-none py-0.5"
      />
      {value ? (
        <button
          onClick={handleClear}
          type="button"
          className="text-text-muted hover:text-text-primary p-0.5 rounded-md transition-colors duration-150 outline-none"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      ) : (
        <span className="hidden sm:inline-flex items-center text-[10px] font-bold text-text-muted bg-muted px-1.5 py-0.5 rounded-md border border-border select-none">
          ⌘K
        </span>
      )}
    </div>
  );
}

export default SearchBar;
