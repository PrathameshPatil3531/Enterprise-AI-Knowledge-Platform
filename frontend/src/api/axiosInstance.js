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
 */

import axios from 'axios'

const axiosInstance = axios.create({
  baseURL: '/api/v1',  // Proxied to FastAPI via Vite (dev) or Nginx (prod)
  timeout: 30000,      // 30 seconds (generous for AI endpoints)
  headers: {
    'Content-Type': 'application/json',
  },
})

// ---------------------------------------------------------------------------
// Request Interceptor
// Runs before EVERY outgoing request.
// Attaches the JWT access token to the Authorization header.
// ---------------------------------------------------------------------------
axiosInstance.interceptors.request.use(
  (config) => {
    // Read token from memory/localStorage
    // In Milestone 2, this will read from the auth store (React Context/Zustand)
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ---------------------------------------------------------------------------
// Response Interceptor
// Runs on EVERY incoming response.
// Handles expired tokens globally — no need to handle 401 in every component.
// ---------------------------------------------------------------------------
axiosInstance.interceptors.response.use(
  // Success: pass response through unchanged
  (response) => response,

  // Error: handle specific status codes
  async (error) => {
    const originalRequest = error.config

    // 401 Unauthorized — token expired or invalid
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true  // Prevent infinite retry loop

      // TODO (Milestone 2): Implement token refresh logic here
      // const newToken = await refreshAccessToken()
      // originalRequest.headers.Authorization = `Bearer ${newToken}`
      // return axiosInstance(originalRequest)

      // For now: redirect to login on 401
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }

    return Promise.reject(error)
  }
)

export default axiosInstance
