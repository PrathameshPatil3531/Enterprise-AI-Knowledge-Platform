/**
 * App.jsx — Root Application Component
 *
 * Responsibilities:
 * - Initialize authentication on app mount (silent token refresh)
 * - Wrap the entire app in BrowserRouter (React Router)
 * - Render the AppRouter which defines all page routes
 *
 * Auth Initialization:
 *   On mount, we call initAuth() which attempts to refresh the access token
 *   using the HTTP-only refresh cookie. If the cookie exists and is valid,
 *   the user gets a new access token and their session is restored.
 *   This prevents the "flash of login page" on page refresh.
 */

import { useEffect } from 'react'
import { BrowserRouter } from 'react-router-dom'
import AppRouter from './router/AppRouter'
import useAuthStore from './store/authStore'

function App() {
  const initAuth = useAuthStore((s) => s.initAuth)

  useEffect(() => {
    initAuth()
  }, [initAuth])

  return (
    <BrowserRouter>
      <AppRouter />
    </BrowserRouter>
  )
}

export default App
