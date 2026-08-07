import React from 'react';
import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import * as LucideIcons from 'lucide-react';
import { cn } from '@/utils';
import Badge from '@/components/ui/Badge';

export function NavigationItem({
  label,
  icon: iconName,
  path,
  badge,
  collapsed = false,
  onClick,
  ...props
}) {
  const IconComponent = LucideIcons[iconName] || LucideIcons.HelpCircle;

  return (
    <NavLink
      to={path}
      onClick={onClick}
      className={({ isActive }) =>
        cn(
          'flex items-center gap-3 px-4 py-3 text-sm font-semibold rounded-xl transition-all duration-200 select-none relative group cursor-pointer outline-none',
          isActive
            ? 'text-white shadow-button'
            : 'text-text-secondary hover:text-text-primary hover:bg-muted/50',
          collapsed ? 'justify-center px-2' : ''
        )
      }
      {...props}
    >
      {({ isActive }) => (
        <>
          {isActive && (
            <motion.div
              layoutId="sidebarActiveBackground"
              className="absolute inset-0 bg-gradient-primary rounded-xl -z-10"
              transition={{ type: 'spring', stiffness: 380, damping: 30 }}
            />
          )}
          <IconComponent
            className={cn(
              'h-5 w-5 flex-shrink-0 transition-transform duration-200 group-hover:scale-105',
              isActive ? 'text-white' : 'text-text-secondary group-hover:text-text-primary'
            )}
          />
          {!collapsed && (
            <span className="flex-1 truncate">{label}</span>
          )}
          {!collapsed && badge && (
            <Badge variant={isActive ? 'neutral' : 'primary'} size="sm" className="ml-auto flex-shrink-0">
              {badge}
            </Badge>
          )}
        </>
      )}
    </NavLink>
  );
}

export default NavigationItem;
