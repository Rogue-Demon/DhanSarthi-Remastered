import React from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '@/hooks'
import { ROUTE_PATHS } from '@/constants'
import Loading from '@/components/common/Loading'

export function PublicRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()

  // Show loading spinner while checking auth status
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <Loading size="large" />
      </div>
    )
  }

  // Redirect to dashboard if already authenticated
  if (isAuthenticated) {
    return <Navigate to={ROUTE_PATHS.DASHBOARD} replace />
  }

  return children
}

export default PublicRoute
