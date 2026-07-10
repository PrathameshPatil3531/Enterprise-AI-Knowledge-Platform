/**
 * GuestRoute.jsx — Route Guard for Unauthenticated Users
 *
 * Wraps routes that should only be accessible when NOT logged in (Login, Register).
 *
 * Behavior:
 * - isLoading=true    → Show loading spinner (initAuth is checking session)
 * - Authenticated     → Redirect to /dashboard (already logged in)
 * - Not authenticated → Render the auth page (Login / Register)
 *
 * WHY this component?
 * - Prevents the confusing UX of seeing a login form when already logged in
 * - If a user navigates to /login while authenticated, they're sent to /dashboard
 */

import { Navigate } from 'react-router-dom'
import useAuthStore from '../store/authStore'

function GuestRoute({ children }) {
  const user = useAuthStore((s) => s.user)
  const isLoading = useAuthStore((s) => s.isLoading)

  // Still checking session — show loading
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-3 border-primary-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-slate-400 text-sm">Loading...</p>
        </div>
      </div>
    )
  }

  // Already authenticated — redirect to dashboard
  if (user) {
    return <Navigate to="/dashboard" replace />
  }

  // Not authenticated — show the auth page
  return children
}

export default GuestRoute
