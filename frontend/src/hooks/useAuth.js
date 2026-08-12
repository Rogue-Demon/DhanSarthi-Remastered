import { useContext } from 'react'
import { AuthContext } from '@/contexts'

/**
 * useAuth hook
 *
 * Provides access to the centralized authentication state (user, status, login, logout, etc.)
 */
export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export default useAuth
