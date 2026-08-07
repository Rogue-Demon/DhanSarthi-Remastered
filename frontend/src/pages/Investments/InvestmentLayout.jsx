import React from 'react';
import { Outlet } from 'react-router-dom';
import { PageTransition } from '@/components/motion';
import InvestmentSidebar from './InvestmentSidebar';
import InvestmentHeader from './InvestmentHeader';
import InvestmentBreadcrumb from './InvestmentBreadcrumb';

/**
 * InvestmentLayout Component
 *
 * Primary wrapper layout coordinating the secondary navigation sidebar (tabs)
 * and subpage outlets for all nested Investments module routes.
 */
export function InvestmentLayout() {
  return (
    <PageTransition className="flex flex-col md:flex-row min-h-[calc(100vh-4rem)] w-full bg-background select-none">
      {/* Secondary Left Navigation Sidebar (collapses into horizontal tab bar on mobile) */}
      <InvestmentSidebar />

      {/* Main Content Area */}
      <main className="flex-1 p-4 md:p-8 flex flex-col gap-6 overflow-y-auto max-w-[1200px]">
        {/* Module breadcrumb path */}
        <InvestmentBreadcrumb />

        {/* Dynamic Search & Actions Toolbar */}
        <InvestmentHeader />

        {/* Render nested lazy routes */}
        <div className="w-full flex-grow mt-2">
          <Outlet />
        </div>
      </main>
    </PageTransition>
  );
}

export default InvestmentLayout;
