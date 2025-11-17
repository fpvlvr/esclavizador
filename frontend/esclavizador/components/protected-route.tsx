"use client"

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/use-auth'
import type { UserRole } from '@/lib/api/generated'

interface ProtectedRouteProps {
  children: React.ReactNode
  requireRole?: UserRole
}

/**
 * Route guard component that requires authentication
 *
 * Redirects to /login if user is not authenticated
 * Optionally enforces role-based access (e.g., boss-only routes)
 */
export function ProtectedRoute({ children, requireRole }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated) {
        router.push('/login')
      } else if (requireRole && user?.role !== requireRole) {
        // User is authenticated but doesn't have required role
        router.push('/')
      }
    }
  }, [isAuthenticated, isLoading, requireRole, user, router])

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  // Show nothing while redirecting
  if (!isAuthenticated) {
    return null
  }

  // Check role if required
  if (requireRole && user?.role !== requireRole) {
    return null
  }

  return <>{children}</>
}
