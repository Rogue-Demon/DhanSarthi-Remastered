import React from 'react';
import { Navigate } from 'react-router-dom';
import { useProfile } from '@/hooks';
import { ROUTE_PATHS } from '@/constants';

/**
 * ProtectedRoute Guard
 * 
 * Verifies that the user has completed onboarding and has an active profile
 * selected. If not, redirects to the onboarding start page.
 */
export function ProtectedRoute({ children }) {
  const { profile, onboardingComplete } = useProfile();

  // Guard: If onboarding is not completed or profile is missing, redirect to onboarding flow
  if (!onboardingComplete || !profile) {
    return <Navigate to={ROUTE_PATHS.ONBOARDING} replace />;
  }

  return children;
}

export default ProtectedRoute;
