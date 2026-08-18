import React from 'react'
import { useProfile } from '@/hooks'
import { getActiveWidgets } from '@/config'
import { StaggerContainer } from '@/components/motion'
import DashboardGrid from './DashboardGrid'
import WidgetRenderer from './WidgetRenderer'
import EmptyDashboard from './EmptyDashboard'

/**
 * DashboardWidgets Component
 *
 * Dynamically resolves, loads, and structures active widgets for the selected
 * user profile within a staggered entrance grid layout.
 */
export function DashboardWidgets({ dashboardData }) {
  const { profile } = useProfile()

  if (!profile) {
    return <EmptyDashboard />
  }

  // Retrieve active widget configurations
  const activeWidgets = getActiveWidgets(profile)

  if (activeWidgets.length === 0) {
    return <EmptyDashboard />
  }

  return (
    <StaggerContainer staggerDelay={0.08} delayChildren={0.1}>
      <DashboardGrid>
        {activeWidgets.map((widgetConfig) => (
          <WidgetRenderer
            key={widgetConfig.id}
            widgetId={widgetConfig.id}
            size={widgetConfig.size}
            dashboardData={dashboardData}
          />
        ))}
      </DashboardGrid>
    </StaggerContainer>
  )
}

export default DashboardWidgets
