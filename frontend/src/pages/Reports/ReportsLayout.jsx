import React from 'react';
import { Outlet } from 'react-router-dom';
import { PageTransition } from '@/components/motion';
import ReportsSidebar from './ReportsSidebar';
import ReportsHeader from './ReportsHeader';
import ReportsBreadcrumb from './ReportsBreadcrumb';

/**
 * ReportsLayout Component
 * Primary layout wrapper coordinating the secondary navigation sidebar
 * and subpage outlets for all nested Reports module routes.
 */
export function ReportsLayout() {
  return (
    <PageTransition className="flex flex-col md:flex-row min-h-[calc(100vh-4rem)] w-full bg-background select-none">
      {/* Secondary Left Navigation Sidebar (collapses into horizontal tab bar on mobile) */}
      <ReportsSidebar />

      {/* Main Content Area */}
      <main className="flex-1 p-4 md:p-8 flex flex-col gap-6 overflow-y-auto max-w-[1200px]">
        {/* Module breadcrumb path */}
        <ReportsBreadcrumb />

        {/* Dynamic Search & Actions Toolbar */}
        <ReportsHeader />

        {/* Render nested lazy routes */}
        <div className="w-full flex-grow mt-2">
          <Outlet />
        </div>
      </main>
    </PageTransition>
  );
}

export default ReportsLayout;
