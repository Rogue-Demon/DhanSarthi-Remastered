import React from 'react'
import { useProfile, useDashboardData } from '@/hooks'
import { PageTransition } from '@/components/motion'
import { DashboardLoader, DashboardBanner, DashboardSummary } from '@/components/dashboard'
import { Button } from '@/components/ui'
import DashboardContainer from './DashboardContainer'
import DashboardHeader from './DashboardHeader'
import DashboardSection from './DashboardSection'
import DashboardWidgets from './DashboardWidgets'
import EmptyDashboard from './EmptyDashboard'

/**
 * Dashboard Page Component
 *
 * Coordinates the full dashboard view. It reads the active profile from Zustand.
 * Triggers a loading skeleton transition upon profile switches, before loading
 * the layout structure based on real backend API flows.
 */
export function Dashboard() {
  const { profile } = useProfile()
  const { data: dashboardData, isLoading, isError, refetch } = useDashboardData()

  if (!profile) {
    return (
      <PageTransition className="p-4 md:p-6 min-h-[80vh] flex items-center justify-center">
        <EmptyDashboard />
      </PageTransition>
    )
  }

  if (isLoading) {
    return (
      <PageTransition>
        <DashboardLoader />
      </PageTransition>
    )
  }

  if (isError) {
    return (
      <PageTransition className="p-4 md:p-6 min-h-[80vh] flex flex-col items-center justify-center gap-4 text-center select-none">
        <div className="h-14 w-14 rounded-full bg-danger/10 text-danger flex items-center justify-center shadow-inner">
          <svg
            className="h-7 w-7"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
        <div className="flex flex-col gap-1.5">
          <h3 className="text-lg font-black text-text-primary uppercase tracking-wide">
            Failed to load Dashboard
          </h3>
          <p className="text-xs font-bold text-text-muted max-w-[280px]">
            Please verify your network connection or try refreshing the workspace.
          </p>
        </div>
        <Button
          variant="primary"
          size="sm"
          onClick={() => refetch()}
          className="font-bold py-2 rounded-xl"
        >
          Retry Connection
        </Button>
      </PageTransition>
    )
  }

  return (
    <PageTransition>
      <DashboardContainer>
        {/* Header row (Greetings, date, actions) */}
        <DashboardHeader />

        {/* Profile-specific welcome banner card */}
        <DashboardBanner dashboardData={dashboardData} />

        {/* Summary Strip (Placeholders metrics) */}
        <DashboardSummary dashboardData={dashboardData} />

        {/* Widgets Grid Section */}
        <DashboardSection
          title="Overview & Operations"
          subtitle="Current active financial monitoring widgets"
        >
          <DashboardWidgets dashboardData={dashboardData} />
        </DashboardSection>
      </DashboardContainer>
    </PageTransition>
  )
}

export default Dashboard
