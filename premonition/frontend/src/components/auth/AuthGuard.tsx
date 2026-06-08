import { useEffect, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { ROUTES } from '@/routes/paths'

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate()
  const location = useLocation()
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null)

  useEffect(() => {
    const token = localStorage.getItem('premonition_access_token')
    if (!token) {
      setIsAuthenticated(false)
      navigate(ROUTES.login, { replace: true, state: { from: location.pathname } })
    } else {
      setIsAuthenticated(true)
    }
  }, [navigate, location])

  if (isAuthenticated === null || !isAuthenticated) {
    return null
  }

  return <>{children}</>
}
