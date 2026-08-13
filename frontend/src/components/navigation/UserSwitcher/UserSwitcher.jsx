import React from 'react'
import { useProfile, useAuth } from '@/hooks'
import { PROFILES } from '@/constants'
import Dropdown, { MenuItem } from '@/components/overlay/Dropdown'
import Avatar from '@/components/ui/Avatar'
import { cn, helpers } from '@/utils'
import { apiClient, ENDPOINTS } from '@/services/api'

export function UserSwitcher({ collapsed = false, className, ...props }) {
  const { profile, setProfile } = useProfile()
  const { user, updateLocalProfile } = useAuth()

  const handleProfileChange = async (selected) => {
    setProfile(selected)
    if (user) {
      try {
        const backendPersona = helpers.mapFrontendToBackendPersona(selected)
        const updated = await apiClient.patch(ENDPOINTS.profile.update, { persona: backendPersona })
        updateLocalProfile(updated)
      } catch (err) {
        console.error('Failed to update persona on backend:', err)
      }
    }
  }

  const dropdownItems = Object.values(PROFILES).map((p) => (
    <MenuItem
      key={p}
      onClick={() => handleProfileChange(p)}
      className={cn(p === profile && 'text-primary bg-primary/5 font-bold')}
    >
      <div className="flex flex-col">
        <span className="text-sm">{p}</span>
      </div>
    </MenuItem>
  ))

  const displayName = user?.profile?.display_name || user?.email?.split('@')[0] || 'User'

  return (
    <div
      className={cn(
        'flex items-center gap-3 w-full border border-border bg-muted/40 p-2.5 rounded-xl',
        className
      )}
      {...props}
    >
      <Dropdown
        menuItems={dropdownItems}
        align={collapsed ? 'left' : 'right'}
        direction="up"
        className="w-full"
      >
        <div className="flex items-center gap-3 w-full justify-between select-none cursor-pointer">
          <div className="flex items-center gap-3">
            <Avatar name={displayName} size="sm" online />
            {!collapsed && (
              <div className="flex flex-col text-left">
                <span className="text-sm font-bold text-text-primary">{displayName}</span>
                <span className="text-[10px] font-bold text-primary uppercase tracking-wider">
                  {profile}
                </span>
              </div>
            )}
          </div>
          {!collapsed && (
            <svg
              className="h-4 w-4 text-text-muted flex-shrink-0"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="2.5"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 9l4 4 4-4" />
            </svg>
          )}
        </div>
      </Dropdown>
    </div>
  )
}

export default UserSwitcher
