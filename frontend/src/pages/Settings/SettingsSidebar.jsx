import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import * as LucideIcons from 'lucide-react';
import { cn } from '@/utils';
import { motion } from 'framer-motion';

export function SettingsSidebar({ className }) {
  const location = useLocation();

  const navItems = [
    { label: 'Profile', path: '/settings/profile', icon: 'User' },
    { label: 'Appearance', path: '/settings/appearance', icon: 'Palette' },
    { label: 'Notifications', path: '/settings/notifications', icon: 'Bell' },
    { label: 'Preferences', path: '/settings/preferences', icon: 'Sliders' },
    { label: 'Privacy', path: '/settings/privacy', icon: 'Shield' },
    { label: 'Security', path: '/settings/security', icon: 'Lock' },
    { label: 'Language', path: '/settings/language', icon: 'Globe' },
    { label: 'Accessibility', path: '/settings/accessibility', icon: 'Eye' },
    { label: 'Data & Export', path: '/settings/data-export', icon: 'Database' },
    { label: 'Integrations', path: '/settings/integrations', icon: 'Plug' },
    { label: 'About', path: '/settings/about', icon: 'Info' },
  ];

  const isActivePath = (path) => {
    if (path === '/settings/profile') {
      return location.pathname === '/settings' || location.pathname === '/settings/profile';
    }
    return location.pathname === path;
  };

  return (
    <aside
      className={cn(
        'flex md:flex-col gap-2 p-2 bg-card border-b md:border-b-0 md:border-r border-border/80 w-full md:w-56 shrink-0 overflow-x-auto md:overflow-x-visible scrollbar-none sticky top-16 z-10 md:h-[calc(100vh-4rem)] md:py-6 md:px-3 text-left select-none',
        className
      )}
    >
      {navItems.map((item) => {
        const IconComponent = LucideIcons[item.icon] || LucideIcons.Settings;
        const active = isActivePath(item.path);

        return (
          <NavLink
            key={item.path}
            to={item.path}
            className={cn(
              'relative flex items-center gap-3 px-4.5 py-3 rounded-xl text-xs font-black uppercase tracking-wider transition-all duration-200 outline-none shrink-0 group',
              active
                ? 'text-primary'
                : 'text-text-muted hover:text-text-secondary hover:bg-muted/40'
            )}
          >
            {active && (
              <motion.div
                layoutId="active-settings-tab"
                className="absolute inset-0 bg-primary/10 border-l-3 border-primary rounded-xl z-[-1]"
                transition={{ type: 'spring', stiffness: 380, damping: 30 }}
              />
            )}
            <IconComponent className={cn('h-4.5 w-4.5 stroke-[2.2] shrink-0', active ? 'text-primary' : 'text-text-muted group-hover:text-text-secondary')} />
            <span>{item.label}</span>
          </NavLink>
        );
      })}
    </aside>
  );
}

export default SettingsSidebar;
