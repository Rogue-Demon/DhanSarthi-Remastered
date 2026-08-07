import React from 'react';
import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import * as LucideIcons from 'lucide-react';
import { cn } from '@/utils';

export function BottomNavigation({ className, ...props }) {
  const bottomBarTargets = [
    { label: 'Home', icon: 'LayoutDashboard', path: '/dashboard' },
    { label: 'Finance', icon: 'Wallet', path: '/finance' },
    { label: 'Advisor', icon: 'Bot', path: '/ai-advisor' },
    { label: 'Invest', icon: 'TrendingUp', path: '/investments' },
    { label: 'Settings', icon: 'Settings', path: '/settings' },
  ];

  return (
    <nav
      className={cn(
        'fixed bottom-0 left-0 right-0 h-16 bg-card/90 backdrop-blur-md border-t border-border flex items-center justify-around px-2 z-35 md:hidden select-none clay-surface-flat shadow-modal',
        className
      )}
      {...props}
    >
      {bottomBarTargets.map((item, index) => {
        const IconComponent = LucideIcons[item.icon] || LucideIcons.HelpCircle;

        return (
          <NavLink
            key={index}
            to={item.path}
            className={({ isActive }) =>
              cn(
                'flex flex-col items-center justify-center gap-1 w-14 h-12 rounded-xl transition-all duration-150 relative text-xs font-semibold',
                isActive ? 'text-primary' : 'text-text-secondary hover:text-text-primary'
              )
            }
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <motion.div
                    layoutId="bottomNavIndicator"
                    className="absolute top-0 h-1 w-6 bg-primary rounded-full"
                    transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                  />
                )}
                <IconComponent className={cn('h-5.5 w-5.5', isActive ? 'text-primary' : 'text-text-secondary')} />
                <span className="text-[9px] truncate max-w-[50px]">{item.label}</span>
              </>
            )}
          </NavLink>
        );
      })}
    </nav>
  );
}

export default BottomNavigation;
