/**
 * authStore.js — Authentication State Management (Zustand)
 *
 * Single source of truth for authentication state.
 * All components read auth state from here. All auth actions go through here.
 *
 * WHY Zustand over React Context?
 * - No provider wrapper needed (less boilerplate)
 * - Components only re-render when their subscribed slice changes
 * - Dead simple API: useAuthStore(state => state.user)
 * - Works outside React components (e.g., in Axios interceptors)
 *
 * SECURITY: Access token is stored in memory only (Zustand state).
 * It is NOT persisted to localStorage, sessionStorage, or cookies.
 * This protects against XSS attacks — a script cannot steal the token.
 * On page refresh, initAuth() silently refreshes via the HTTP-only cookie.
 */

import { create } from 'zustand'
import { loginApi, registerApi, logoutApi, refreshApi, getMeApi } from '../api/authApi'
import { setAuthStore } from '../api/axiosInstance'

const useAuthStore = create((set, get) => ({
  // -----------------------------------------------------------------------
  // State
  // -----------------------------------------------------------------------
  user: null,             // User object from GET /users/me
  accessToken: null,      // JWT access token (in-memory only)
  isLoading: true,        // True during initial auth check (prevents login page flash)
  error: null,            // Last auth error message

  // -----------------------------------------------------------------------
  // ACTIONS
  // -----------------------------------------------------------------------

  /**
   * Login — Authenticate with email and password.
   *
   * Flow:
   * 1. POST /auth/login → receive access_token + refresh cookie
   * 2. Store access_token in memory
   * 3. GET /users/me → fetch user profile
   * 4. Store user in state
   *
   * Throws on failure so the LoginPage can display the error.
   */
  login: async (email, password) => {
    set({ error: null })
    try {
      const { data: tokenData } = await loginApi(email, password)
      set({ accessToken: tokenData.access_token })

      // Fetch user profile with the new token
      const { data: user } = await getMeApi()
      set({ user, isLoading: false })

      return user
    } catch (err) {
      const message = err.response?.data?.detail || 'Login failed. Please try again.'
      set({ error: message, user: null, accessToken: null, isLoading: false })
      throw err
    }
  },

  /**
   * Register — Create a new user account.
   *
   * Does NOT auto-login. Returns the created user data.
   * The RegisterPage redirects to /login with a success message.
   */
  register: async (userData) => {
    set({ error: null })
    try {
      const { data } = await registerApi(userData)
      return data
    } catch (err) {
      const message = err.response?.data?.detail || 'Registration failed. Please try again.'
      set({ error: message })
      throw err
    }
  },

  /**
   * Logout — Revoke refresh token and clear all auth state.
   *
   * The server clears the HTTP-only refresh cookie.
   * We clear the in-memory state.
   */
  logout: async () => {
    try {
      await logoutApi()
    } catch {
      // Ignore errors — we clear local state regardless.
      // The server may be down, but the user should still be "logged out" locally.
    } finally {
      set({ user: null, accessToken: null, error: null, isLoading: false })
    }
  },

  /**
   * Refresh Token — Exchange refresh cookie for a new access token.
   *
   * Called by:
   * 1. initAuth() on app load — to restore session after page refresh
   * 2. Axios 401 interceptor — to silently refresh expired access tokens
   *
   * Returns the new access token string, or null on failure.
   */
  refreshToken: async () => {
    try {
      const { data } = await refreshApi()
      set({ accessToken: data.access_token })
      return data.access_token
    } catch {
      // Refresh failed — user must log in again
      set({ user: null, accessToken: null, isLoading: false })
      return null
    }
  },

  /**
   * Initialize Auth — Called once on app mount.
   *
   * Attempts to restore the user's session by:
   * 1. Calling POST /auth/refresh (uses HTTP-only cookie)
   * 2. If refresh succeeds, fetching the user profile
   * 3. If either fails, the user is unauthenticated (that's fine)
   *
   * This prevents the "flash of login page" on page refresh
   * for users who have a valid refresh token cookie.
   */
  initAuth: async () => {
    set({ isLoading: true })
    try {
      // Attempt silent refresh — this works if the browser has a valid refresh cookie
      const { data: tokenData } = await refreshApi()
      set({ accessToken: tokenData.access_token })

      // Fetch user profile
      const { data: user } = await getMeApi()
      set({ user, isLoading: false })
    } catch {
      // No valid session — that's OK, user will see login page
      set({ user: null, accessToken: null, isLoading: false })
    }
  },

  /**
   * Clear Error — Dismiss the current error message.
   */
  clearError: () => set({ error: null }),
}))

// ---------------------------------------------------------------------------
// Register this store with the Axios interceptor
//
// This breaks the circular dependency:
//   axiosInstance.js exports setAuthStore (no import of authStore)
//   authStore.js imports setAuthStore and calls it after store creation
// ---------------------------------------------------------------------------
setAuthStore(useAuthStore)

export default useAuthStore
