import React, { useState, useEffect } from 'react';
import Modal from '@/components/overlay/Modal';
import { cn } from '@/utils';

export function CommandPalettePlaceholder({ className, ...props }) {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const closePalette = () => setIsOpen(false);

  const commandItems = [
    { category: 'Navigation', label: 'Go to Dashboard', shortcut: 'G + D', icon: 'LayoutDashboard' },
    { category: 'Navigation', label: 'Go to AI Advisor', shortcut: 'G + A', icon: 'Bot' },
    { category: 'Navigation', label: 'Go to Finance Manager', shortcut: 'G + F', icon: 'Wallet' },
    { category: 'Preferences', label: 'Toggle Dark Mode', shortcut: 'T + D', icon: 'Moon' },
    { category: 'Preferences', label: 'Change Active Profile', shortcut: 'C + P', icon: 'User' },
  ];

  return (
    <Modal isOpen={isOpen} onClose={closePalette} size="md" title="Command Menu">
      <div className={cn('flex flex-col gap-4', className)} {...props}>
        <div className="relative flex items-center border border-border bg-muted/40 rounded-xl px-3 py-2">
          <svg className="h-5 w-5 text-text-muted mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            placeholder="Type a command or search..."
            className="w-full bg-transparent text-sm text-text-primary placeholder-text-muted outline-none border-none py-0.5"
            autoFocus
          />
        </div>

        <div className="flex flex-col gap-3 max-h-[300px] overflow-y-auto scrollbar-none pr-1">
          <div className="flex flex-col gap-1.5">
            <span className="text-[10px] font-extrabold text-text-muted uppercase tracking-wider select-none px-2 py-1">
              Suggestions
            </span>
            {commandItems.map((item, idx) => (
              <button
                key={idx}
                onClick={closePalette}
                className="w-full text-left flex items-center justify-between px-3 py-2.5 rounded-xl hover:bg-muted transition-colors duration-150 outline-none select-none cursor-pointer"
              >
                <div className="flex items-center gap-2.5 text-sm font-semibold text-text-secondary">
                  <span>{item.label}</span>
                </div>
                <span className="text-[10px] font-bold text-text-muted bg-muted px-2 py-1 rounded-md border border-border">
                  {item.shortcut}
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </Modal>
  );
}

export default CommandPalettePlaceholder;
