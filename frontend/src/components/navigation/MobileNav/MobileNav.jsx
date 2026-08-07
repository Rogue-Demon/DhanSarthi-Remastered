import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSidebar, useProfile } from '@/hooks';
import { navigationConfig } from '@/config';
import { NavigationItem } from '../NavigationItem/NavigationItem';
import NavigationGroup from '../NavigationGroup';
import UserSwitcher from '../UserSwitcher/UserSwitcher';
import Logo from '@/components/common/Logo';
import BrandText from '@/components/common/BrandText';
import IconButton from '@/components/ui/IconButton';
import { cn } from '@/utils';

export function MobileNav({ className, ...props }) {
  const { mobileOpen, setMobileOpen } = useSidebar();
  const { profile } = useProfile();

  const menuItems = navigationConfig[profile] || [];

  const handleClose = () => setMobileOpen(false);

  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') handleClose();
    };

    if (mobileOpen) {
      document.addEventListener('keydown', handleEscape);
    }
    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [mobileOpen]);

  const closeIcon = (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
    </svg>
  );

  return (
    <AnimatePresence>
      {mobileOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.4 }}
            exit={{ opacity: 0 }}
            onClick={handleClose}
            className="fixed inset-0 bg-black z-40 md:hidden"
          />

          <motion.aside
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{ type: 'spring', stiffness: 380, damping: 30 }}
            className={cn(
              'fixed top-0 left-0 bottom-0 w-72 bg-card border-r border-border p-4 z-50 flex flex-col md:hidden select-none clay-surface shadow-modal',
              className
            )}
            {...props}
          >
            <div className="flex items-center justify-between h-14 px-2.5">
              <div className="flex items-center gap-3">
                <Logo size="md" />
                <BrandText size="lg" />
              </div>
              <IconButton icon={closeIcon} onClick={handleClose} tooltip="Close Menu" size="sm" />
            </div>

            <div className="flex-1 overflow-y-auto mt-6 scrollbar-none flex flex-col gap-6">
              <NavigationGroup>
                {menuItems.map((item, index) => (
                  <NavigationItem
                    key={index}
                    label={item.label}
                    icon={item.icon}
                    path={item.path}
                    badge={item.badge}
                    onClick={handleClose}
                  />
                ))}
              </NavigationGroup>
            </div>

            <div className="mt-auto pt-4 border-t border-border flex flex-col gap-4">
              <UserSwitcher />
              <div className="px-2.5">
                <span className="text-[10px] text-text-muted font-bold tracking-wider">VERSION 1.0.0</span>
              </div>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}

export default MobileNav;
