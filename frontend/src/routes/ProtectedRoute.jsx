import React from 'react'
import { Navigate } from 'react-router-dom'
import { useProfile, useAuth } from '@/hooks'
import { ROUTE_PATHS } from '@/constants'
import Loading from '@/components/common/Loading'

/**
 * ProtectedRoute Guard
 *
 * Verifies that the user is authenticated, has completed onboarding, and has an active profile
 * selected. If not, redirects to the appropriate page.
 */
export function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()
  const { profile, onboardingComplete } = useProfile()

  // Show loading spinner while checking auth status
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <Loading size="large" />
      </div>
    )
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to={ROUTE_PATHS.LOGIN} replace />
  }

  // Guard: If onboarding is not completed or profile is missing, redirect to onboarding flow
  if (!onboardingComplete || !profile) {
    return <Navigate to={ROUTE_PATHS.ONBOARDING} replace />
  }

  return children
}

export default ProtectedRoute
