import React from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { queryClient } from '@/lib'
import {
  ThemeProvider,
  AppContextProvider,
  AuthProvider,
  NotificationPlaceholderProvider,
  ModalPlaceholderProvider,
} from '@/providers'

export function AppProviders({ children }) {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AppContextProvider>
          <AuthProvider>
            <NotificationPlaceholderProvider>
              <ModalPlaceholderProvider>
                {children}
                {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
              </ModalPlaceholderProvider>
            </NotificationPlaceholderProvider>
          </AuthProvider>
        </AppContextProvider>
      </ThemeProvider>
    </QueryClientProvider>
  )
}

export default AppProviders
