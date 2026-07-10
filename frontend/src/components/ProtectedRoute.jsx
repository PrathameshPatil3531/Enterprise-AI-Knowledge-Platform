/**
 * ProtectedRoute.jsx — Route Guard for Authenticated Users
 *
 * Wraps routes that require authentication (Dashboard, Documents, Chat).
 *
 * Behavior:
 * - isLoading=true  → Show loading spinner (initAuth is checking session)
 * - Authenticated   → Render the protected content
 * - Not authenticated → Redirect to /login
 *
 * Usage:
 *   <Route path="/dashboard" element={
 *     <ProtectedRoute><DashboardPage /></ProtectedRoute>
 *   } />
 */

import { Navigate } from 'react-router-dom'
import useAuthStore from '../store/authStore'

function ProtectedRoute({ children }) {
  const user = useAuthStore((s) => s.user)
  const isLoading = useAuthStore((s) => s.isLoading)

  // Still checking if user has a valid session — show loading
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

  // Not authenticated — redirect to login
  if (!user) {
    return <Navigate to="/login" replace />
  }

  // Authenticated — render the protected content
  return children
}

export default ProtectedRoute
