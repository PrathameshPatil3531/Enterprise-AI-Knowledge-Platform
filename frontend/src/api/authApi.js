/**
 * authApi.js — Authentication API Calls
 *
 * All auth-related HTTP requests. Each function returns an Axios promise.
 * The Zustand store calls these — components never call them directly.
 *
 * Note: POST /auth/refresh uses the HTTP-only cookie automatically.
 * The browser attaches the cookie because the cookie's path is /api/v1/auth.
 */

import axiosInstance from './axiosInstance'

/**
 * POST /auth/login
 * Returns: { access_token, token_type }
 * Side effect: Server sets refresh token cookie (HTTP-only)
 */
export const loginApi = (email, password) =>
  axiosInstance.post('/auth/login', { email, password })

/**
 * POST /auth/register
 * Returns: { id, email, full_name, is_active, is_verified, ... }
 */
export const registerApi = (data) =>
  axiosInstance.post('/auth/register', data)

/**
 * POST /auth/refresh
 * The refresh token cookie is sent automatically by the browser.
 * Returns: { access_token, token_type }
 * Side effect: Server rotates the refresh token cookie
 */
export const refreshApi = () =>
  axiosInstance.post('/auth/refresh')

/**
 * POST /auth/logout
 * Revokes the current refresh token and clears the cookie.
 */
export const logoutApi = () =>
  axiosInstance.post('/auth/logout')

/**
 * GET /users/me
 * Returns the authenticated user's profile.
 * Requires: Authorization: Bearer <access_token>
 */
export const getMeApi = () =>
  axiosInstance.get('/users/me')
