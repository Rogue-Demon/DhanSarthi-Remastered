import React from 'react';
import { Outlet } from 'react-router-dom';
import { PageTransition } from '@/components/motion';
import SettingsSidebar from './SettingsSidebar';
import SettingsHeader from './SettingsHeader';
import SettingsBreadcrumb from './SettingsBreadcrumb';

export function SettingsLayout() {
  return (
    <PageTransition className="flex flex-col md:flex-row min-h-[calc(100vh-4rem)] w-full bg-background select-none">
      <SettingsSidebar />
      <main className="flex-1 p-4 md:p-8 flex flex-col gap-6 overflow-y-auto max-w-[1200px]">
        <SettingsBreadcrumb />
        <SettingsHeader />
        <div className="w-full flex-grow mt-2">
          <Outlet />
        </div>
      </main>
    </PageTransition>
  );
}

export default SettingsLayout;
