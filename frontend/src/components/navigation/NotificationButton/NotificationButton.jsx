import React from 'react';
import Dropdown, { MenuItem } from '@/components/overlay/Dropdown';
import NotificationBadge from '@/components/common/NotificationBadge';
import IconButton from '@/components/ui/IconButton';

export function NotificationButton({ className, ...props }) {
  const notificationCount = 3;

  const bellIcon = (
    <div className="relative">
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
      </svg>
      <NotificationBadge count={notificationCount} />
    </div>
  );

  const notificationItems = [
    <MenuItem key="1" className="flex flex-col items-start gap-1 p-3">
      <span className="text-xs font-bold text-primary">System Notification</span>
      <span className="text-xs text-text-secondary">Welcome to DhanSarthi! Let's get started.</span>
      <span className="text-[10px] text-text-muted">Just now</span>
    </MenuItem>,
    <MenuItem key="2" className="flex flex-col items-start gap-1 p-3 border-t border-border">
      <span className="text-xs font-bold text-success">Financial Goal Achieved</span>
      <span className="text-xs text-text-secondary">Your monthly savings goal has been hit! 🥳</span>
      <span className="text-[10px] text-text-muted">2 hours ago</span>
    </MenuItem>,
    <MenuItem key="3" className="flex flex-col items-start gap-1 p-3 border-t border-border">
      <span className="text-xs font-bold text-warning">Advisor Alert</span>
      <span className="text-xs text-text-secondary">Smart portfolio rebalancing is recommended.</span>
      <span className="text-[10px] text-text-muted">Yesterday</span>
    </MenuItem>,
  ];

  return (
    <Dropdown menuItems={notificationItems} align="right" className={className} {...props}>
      <IconButton icon={bellIcon} size="md" tooltip="Notifications" />
    </Dropdown>
  );
}

export default NotificationButton;
