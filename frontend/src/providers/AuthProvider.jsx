import React, { useState, useEffect } from 'react'
import { AuthContext } from '@/contexts'
import { STORAGE_KEYS } from '@/constants'
import { apiClient, ENDPOINTS } from '@/services/api'
import { useProfileStore } from '@/store'
import { helpers } from '@/utils'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [status, setStatus] = useState('INITIALIZING') // INITIALIZING | AUTHENTICATED | UNAUTHENTICATED | AUTH_ERROR
  const [error, setError] = useState(null)

  const resetProfileStore = useProfileStore((state) => state.resetOnboarding)

  // Restore session on mount
  useEffect(() => {
    const restoreSession = async () => {
      const token = localStorage.getItem(STORAGE_KEYS.AUTH)
      if (!token) {
        setStatus('UNAUTHENTICATED')
        return
      }

      try {
        const userData = await apiClient.get(ENDPOINTS.auth.me)
        try {
          const profileData = await apiClient.get(ENDPOINTS.profile.get)
          userData.profile = profileData
          if (profileData && profileData.persona) {
            const frontendPersona = helpers.mapBackendToFrontendPersona(profileData.persona)
            useProfileStore.getState().setProfile(frontendPersona)
            useProfileStore.getState().completeOnboarding()
          }
        } catch (profileErr) {
          console.error('Failed to fetch user profile:', profileErr)
        }
        setUser(userData)
        setStatus('AUTHENTICATED')
      } catch (err) {
        console.error('Session restoration failed:', err)
        // Clear invalid token
        localStorage.removeItem(STORAGE_KEYS.AUTH)
        setUser(null)
        setStatus('UNAUTHENTICATED')
      }
    }

    restoreSession()
  }, [])

  // Login handler
  const login = async (email, password) => {
    setStatus('INITIALIZING')
    setError(null)
    try {
      const data = await apiClient.post(ENDPOINTS.auth.login, { email, password })

      // Save token (matching interceptor behavior of using JSON stringification)
      localStorage.setItem(STORAGE_KEYS.AUTH, JSON.stringify(data.access_token))

      // Fetch user profile
      const userData = await apiClient.get(ENDPOINTS.auth.me)
      try {
        let profileData = await apiClient.get(ENDPOINTS.profile.get)

        // Sync local pre-login onboarding profile selection with backend if different
        const localProfile = useProfileStore.getState().profile
        if (localProfile && profileData && profileData.persona) {
          const backendLocalPersona = helpers.mapFrontendToBackendPersona(localProfile)
          if (profileData.persona !== backendLocalPersona) {
            try {
              const updatedProfile = await apiClient.patch(ENDPOINTS.profile.update, {
                persona: backendLocalPersona,
              })
              profileData = updatedProfile
            } catch (patchErr) {
              console.error('Failed to sync local profile selection to backend:', patchErr)
            }
          }
        }

        userData.profile = profileData
        if (profileData && profileData.persona) {
          const frontendPersona = helpers.mapBackendToFrontendPersona(profileData.persona)
          useProfileStore.getState().setProfile(frontendPersona)
          useProfileStore.getState().completeOnboarding()
        }
      } catch (profileErr) {
        console.error('Failed to fetch user profile in login:', profileErr)
      }
      setUser(userData)
      setStatus('AUTHENTICATED')
      return userData
    } catch (err) {
      console.error('Login failed:', err)
      setError(err.message || 'Login failed. Please check your credentials.')
      setStatus('AUTH_ERROR')
      throw err
    }
  }

  // Register handler
  const register = async (email, password) => {
    setError(null)
    try {
      const userData = await apiClient.post(ENDPOINTS.auth.register, { email, password })
      return userData
    } catch (err) {
      console.error('Registration failed:', err)
      setError(err.message || 'Registration failed.')
      throw err
    }
  }

  // Logout handler
  const logout = async () => {
    try {
      // Fire-and-forget logout request to backend
      await apiClient.post(ENDPOINTS.auth.logout).catch(() => {})
    } catch (_) {
      // Ignored: stateless logout cleanup should continue regardless of server response
    }

    // Clear local authentication and profile states
    localStorage.removeItem(STORAGE_KEYS.AUTH)
    localStorage.removeItem(STORAGE_KEYS.PROFILE)
    localStorage.removeItem(STORAGE_KEYS.ONBOARDING_COMPLETE)

    // Reset the profile store in Zustand
    resetProfileStore()

    setUser(null)
    setStatus('UNAUTHENTICATED')
    setError(null)
  }

  const isAuthenticated = status === 'AUTHENTICATED'
  const loading = status === 'INITIALIZING'

  const updateLocalProfile = (updatedProfile) => {
    setUser((prev) => (prev ? { ...prev, profile: updatedProfile } : null))
    if (updatedProfile && updatedProfile.persona) {
      const frontendPersona = helpers.mapBackendToFrontendPersona(updatedProfile.persona)
      useProfileStore.getState().setProfile(frontendPersona)
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        status,
        isAuthenticated,
        loading,
        error,
        login,
        register,
        logout,
        updateLocalProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export default AuthProvider
