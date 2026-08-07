import React, { useState, useEffect } from 'react';
import { useProfile } from '@/hooks';
import { PageTransition } from '@/components/motion';
import { DashboardLoader, DashboardBanner, DashboardSummary } from '@/components/dashboard';
import DashboardContainer from './DashboardContainer';
import DashboardHeader from './DashboardHeader';
import DashboardSection from './DashboardSection';
import DashboardWidgets from './DashboardWidgets';
import EmptyDashboard from './EmptyDashboard';

/**
 * Dashboard Page Component
 *
 * Coordinates the full dashboard view. It reads the active profile from Zustand.
 * Triggers a brief, premium loading skeleton transition upon profile switches
 * to simulate dynamic widget database query delays, before loading the layout
 * structure.
 */
export function Dashboard() {
  const { profile } = useProfile();
  const [loading, setLoading] = useState(true);

  // Trigger a brief skeleton loading animation whenever the profile switches
  useEffect(() => {
    if (!profile) {
      setLoading(false);
      return;
    }

    setLoading(true);
    const timer = setTimeout(() => {
      setLoading(false);
    }, 450); // Premium micro-delay simulation

    return () => clearTimeout(timer);
  }, [profile]);

  if (!profile) {
    return (
      <PageTransition className="p-4 md:p-6 min-h-[80vh] flex items-center justify-center">
        <EmptyDashboard />
      </PageTransition>
    );
  }

  return (
    <PageTransition>
      {loading ? (
        /* Skeletons Loader view during switches */
        <DashboardLoader />
      ) : (
        /* Real Dashboard Layout once loaded */
        <DashboardContainer>
          {/* Header row (Greetings, date, actions) */}
          <DashboardHeader />

          {/* Profile-specific welcome banner card */}
          <DashboardBanner />

          {/* Summary Strip (Placeholders metrics) */}
          <DashboardSummary />

          {/* Widgets Grid Section */}
          <DashboardSection
            title="Overview & Operations"
            subtitle="Current active financial monitoring widgets"
          >
            <DashboardWidgets />
          </DashboardSection>
        </DashboardContainer>
      )}
    </PageTransition>
  );
}

export default Dashboard;
