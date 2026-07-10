/**
 * axiosInstance.js — Configured Axios HTTP Client
 *
 * WHY a custom Axios instance instead of using axios directly?
 * - Centralized base URL: change one line, all API calls update
 * - Request interceptor: automatically adds Authorization header to every request
 * - Response interceptor: handles 401 errors globally (trigger token refresh)
 * - Consistent timeout and headers across all API calls
 * - DRY: no need to set Authorization header in every individual API call
 *
 * This is the ONLY Axios instance in the app.
 * All other API files import this instance.
 *
 * CIRCULAR DEPENDENCY NOTE:
 * axiosInstance ← authApi ← authStore → authApi → axiosInstance
 * To break this cycle, the auth store is injected at runtime via
 * setAuthStore(), called from authStore.js after it's created.
 */

import axios from 'axios'

const axiosInstance = axios.create({
  baseURL: '/api/v1',  // Proxied to FastAPI via Vite (dev) or Nginx (prod)
  timeout: 30000,      // 30 seconds (generous for AI endpoints)
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // REQUIRED: Send HTTP-only cookies (refresh token) with requests
})

// ---------------------------------------------------------------------------
// Auth Store Reference
//
// Set at runtime by authStore.js to break the circular dependency.
// Before the store is injected, requests go out without auth headers.
// ---------------------------------------------------------------------------
let authStoreRef = null

export function setAuthStore(store) {
  authStoreRef = store
}

// ---------------------------------------------------------------------------
// Token Refresh Queue
//
// When multiple requests fail with 401 simultaneously (e.g., a page loads
// 3 API calls at once, and all get 401 because the token just expired),
// we must NOT send 3 refresh requests. That would:
//   1. Waste server resources
//   2. Cause token rotation conflicts (first refresh revokes the old token,
//      second refresh finds a revoked token → reuse detection → all sessions killed)
//
// Solution: The first 401 triggers a refresh. All subsequent 401s during that
// refresh period are queued and resolved once the new token arrives.
// ---------------------------------------------------------------------------
let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error)
    } else {
      resolve(token)
    }
  })
  failedQueue = []
}

// ---------------------------------------------------------------------------
// Request Interceptor
// Runs before EVERY outgoing request.
// Attaches the JWT access token to the Authorization header.
//
// Reads from the Zustand store (in-memory) — NOT localStorage.
// ---------------------------------------------------------------------------
axiosInstance.interceptors.request.use(
  (config) => {
    if (authStoreRef) {
      const token = authStoreRef.getState().accessToken
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ---------------------------------------------------------------------------
// Response Interceptor
// Runs on EVERY incoming response.
// Handles expired tokens globally — no need to handle 401 in every component.
//
// Token Refresh Flow:
// 1. Request fails with 401 (access token expired)
// 2. Call POST /auth/refresh (uses HTTP-only cookie — no token needed)
// 3. Server returns new access_token + rotates refresh cookie
// 4. Update Zustand store with new access token
// 5. Retry the original failed request with the new token
// 6. If refresh fails → clear auth state, redirect to /login
// ---------------------------------------------------------------------------
axiosInstance.interceptors.response.use(
  // Success: pass response through unchanged
  (response) => response,

  // Error: handle specific status codes
  async (error) => {
    const originalRequest = error.config

    // Only handle 401s, and skip retry for refresh/login/register endpoints
    // (those should surface their own errors, not trigger a refresh loop)
    const isAuthEndpoint = originalRequest.url?.includes('/auth/refresh') ||
                           originalRequest.url?.includes('/auth/login') ||
                           originalRequest.url?.includes('/auth/register')

    if (error.response?.status !== 401 || originalRequest._retry || isAuthEndpoint) {
      return Promise.reject(error)
    }

    if (!authStoreRef) {
      return Promise.reject(error)
    }

    // If a refresh is already in progress, queue this request
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject })
      }).then((token) => {
        originalRequest.headers.Authorization = `Bearer ${token}`
        return axiosInstance(originalRequest)
      }).catch((err) => {
        return Promise.reject(err)
      })
    }

    originalRequest._retry = true
    isRefreshing = true

    try {
      // Attempt token refresh
      const newToken = await authStoreRef.getState().refreshToken()

      if (newToken) {
        // Refresh succeeded — retry the original request and process the queue
        processQueue(null, newToken)
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return axiosInstance(originalRequest)
      } else {
        // Refresh failed — reject all queued requests
        processQueue(new Error('Session expired'))
        window.location.href = '/login'
        return Promise.reject(error)
      }
    } catch (refreshError) {
      processQueue(refreshError)
      window.location.href = '/login'
      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  }
)

export default axiosInstance
