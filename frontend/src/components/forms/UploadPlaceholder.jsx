import React, { useState } from 'react';
import { cn } from '@/utils';

export const UploadPlaceholder = ({
  className,
  onFileDrop,
  title = 'Upload a file',
  description = 'Drag and drop or click to upload',
  ...props
}) => {
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      if (onFileDrop) onFileDrop(e.dataTransfer.files);
    }
  };

  return (
    <div
      onDragEnter={handleDrag}
      onDragOver={handleDrag}
      onDragLeave={handleDrag}
      onDrop={handleDrop}
      className={cn(
        'border-2 border-dashed border-border rounded-xl p-8 flex flex-col items-center justify-center text-center gap-2 cursor-pointer transition-colors duration-200 select-none bg-card hover:bg-muted/40',
        dragActive && 'border-primary bg-primary/5',
        className
      )}
      {...props}
    >
      <div className="rounded-xl bg-primary/10 text-primary p-3 w-fit mb-2 flex items-center justify-center">
        <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
        </svg>
      </div>
      <span className="font-bold text-text-primary text-base">{title}</span>
      <p className="text-sm text-text-secondary">{description}</p>
    </div>
  );
};

export default UploadPlaceholder;
