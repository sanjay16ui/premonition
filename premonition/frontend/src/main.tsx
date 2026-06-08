import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider } from 'react-router-dom'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { Notifications } from '@/components/common/Notifications'
import { router } from '@/routes'
import { useThemeStore } from '@/store/themeStore'
import './index.css'

// Apply persisted theme before first render
useThemeStore.getState().setMode(useThemeStore.getState().mode)

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 10_000,
      refetchOnWindowFocus: true,
    },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
        <Notifications />
      </QueryClientProvider>
    </ErrorBoundary>
  </StrictMode>,
)
