import React from 'react';
import { motion } from 'framer-motion';
import { useSidebar, useProfile } from '@/hooks';
import { navigationConfig } from '@/config';
import { NavigationItem } from '../NavigationItem/NavigationItem';
import NavigationGroup from '../NavigationGroup';
import UserSwitcher from '../UserSwitcher/UserSwitcher';
import Logo from '@/components/common/Logo';
import BrandText from '@/components/common/BrandText';
import IconButton from '@/components/ui/IconButton';
import { cn } from '@/utils';

export function Sidebar({ className, ...props }) {
  const { collapsed, toggleSidebar } = useSidebar();
  const { profile } = useProfile();

  const menuItems = navigationConfig[profile] || [];

  const sidebarWidthVariants = {
    expanded: { width: 256, transition: { type: 'spring', stiffness: 350, damping: 35 } },
    collapsed: { width: 80, transition: { type: 'spring', stiffness: 350, damping: 35 } },
  };

  const collapseIcon = (
    <svg className={cn('h-5 w-5 transition-transform duration-200', collapsed && 'rotate-180')} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
    </svg>
  );

  return (
    <motion.aside
      initial={collapsed ? 'collapsed' : 'expanded'}
      animate={collapsed ? 'collapsed' : 'expanded'}
      variants={sidebarWidthVariants}
      className={cn(
        'hidden md:flex flex-col h-screen fixed top-0 left-0 bg-card border-r border-border p-4 select-none z-30 clay-surface shrink-0',
        className
      )}
      {...props}
    >
      {/* Brand Header */}
      <div className="flex items-center gap-3 h-14 px-2.5">
        <Logo size="md" />
        {!collapsed && <BrandText size="lg" />}
      </div>

      {/* Main Navigation - Scrollable */}
      <div className="flex-1 overflow-y-auto mt-6 scrollbar-none flex flex-col gap-6">
        <NavigationGroup collapsed={collapsed}>
          {menuItems.map((item, index) => (
            <NavigationItem
              key={index}
              label={item.label}
              icon={item.icon}
              path={item.path}
              badge={item.badge}
              collapsed={collapsed}
            />
          ))}
        </NavigationGroup>
      </div>

      {/* User Switcher Card */}
      <div className="mt-auto pt-4 border-t border-border flex flex-col gap-4">
        <UserSwitcher collapsed={collapsed} />
        
        {/* Toggle & Version Footer */}
        <div className="flex items-center justify-between px-2.5">
          {!collapsed && (
            <span className="text-[10px] text-text-muted font-bold tracking-wider">VERSION 1.0.0</span>
          )}
          <IconButton
            icon={collapseIcon}
            onClick={toggleSidebar}
            tooltip={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            size="sm"
            className="ml-auto"
          />
        </div>
      </div>
    </motion.aside>
  );
}

export default Sidebar;
