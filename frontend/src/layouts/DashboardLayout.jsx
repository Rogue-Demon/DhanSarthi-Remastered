import React from 'react';
import { Outlet } from 'react-router-dom';
import { useSidebar } from '@/hooks';
import {
  Sidebar,
  Header,
  MobileNav,
  BottomNavigation,
  CommandPalettePlaceholder
} from '@/components/navigation';
import { cn } from '@/utils';

export default function DashboardLayout() {
  const { collapsed } = useSidebar();

  return (
    <div className="flex min-h-screen bg-background">
      {/* Sidebar - Desktop/Laptop */}
      <Sidebar />

      {/* Mobile Drawer Drawer */}
      <MobileNav />

      {/* Main Content Area Container */}
      <div
        className={cn(
          'flex flex-1 flex-col min-h-screen transition-all duration-300 ease-in-out pb-16 md:pb-0',
          collapsed ? 'md:pl-20' : 'md:pl-64'
        )}
      >
        {/* Header - Sticky */}
        <Header />

        {/* Dynamic Outlet Pages */}
        <main className="flex-1 p-4 md:p-6 overflow-x-hidden">
          <Outlet />
        </main>
      </div>

      {/* Bottom Navigation - Mobile only */}
      <BottomNavigation />

      {/* Command Palette dialog triggerable on ⌘K / Ctrl+K */}
      <CommandPalettePlaceholder />
    </div>
  );
}
