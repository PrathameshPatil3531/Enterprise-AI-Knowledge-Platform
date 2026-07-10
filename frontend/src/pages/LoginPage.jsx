/**
 * LoginPage.jsx — User Authentication Page
 *
 * Premium dark-mode login with:
 * - Animated gradient background
 * - Glassmorphic form card
 * - Email + password fields with validation
 * - Loading state on submit
 * - API error display
 * - Link to Register page
 */

import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import useAuthStore from '../store/authStore'

function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const login = useAuthStore((s) => s.login)
  const clearError = useAuthStore((s) => s.clearError)
  const storeError = useAuthStore((s) => s.error)

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  // Success message from registration redirect
  const successMessage = location.state?.message || null

  const handleSubmit = async (e) => {
    e.preventDefault()
    clearError()
    setIsSubmitting(true)

    try {
      await login(email, password)
      // Redirect to the page the user was trying to access, or dashboard
      const from = location.state?.from || '/dashboard'
      navigate(from, { replace: true })
    } catch {
      // Error is set in the store by the login action
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="login-page">
      {/* Animated gradient background */}
      <div className="auth-bg" />

      <div className="auth-container">
        {/* Branding */}
        <div className="auth-branding">
          <div className="auth-logo">
            <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect width="40" height="40" rx="12" fill="url(#logo-gradient)" />
              <path d="M12 28L20 12L28 28H12Z" fill="white" fillOpacity="0.9" />
              <path d="M16 24L20 16L24 24H16Z" fill="url(#logo-gradient)" fillOpacity="0.5" />
              <defs>
                <linearGradient id="logo-gradient" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#4f6ef7" />
                  <stop offset="1" stopColor="#8b5cf6" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <h1 className="auth-title">Welcome back</h1>
          <p className="auth-subtitle">
            Sign in to your Enterprise AI Knowledge Platform
          </p>
        </div>

        {/* Success message (from registration) */}
        {successMessage && (
          <div className="auth-success-message">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 1C4.13 1 1 4.13 1 8s3.13 7 7 7 7-3.13 7-7S11.87 1 8 1zm3.71 5.29l-4 4a1 1 0 01-1.42 0l-2-2a1 1 0 011.42-1.42L7 8.17l3.29-3.29a1 1 0 011.42 1.42z" fill="#34d399" />
            </svg>
            {successMessage}
          </div>
        )}

        {/* Error message */}
        {storeError && (
          <div className="auth-error-message">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 1C4.13 1 1 4.13 1 8s3.13 7 7 7 7-3.13 7-7S11.87 1 8 1zm-.5 3h1v5h-1V4zm.5 8a.75.75 0 110-1.5.75.75 0 010 1.5z" fill="#f87171" />
            </svg>
            {storeError}
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="auth-form" id="login-form">
          {/* Email Field */}
          <div className="form-group">
            <label htmlFor="login-email" className="form-label">
              Email address
            </label>
            <input
              id="login-email"
              type="email"
              className="input-field"
              placeholder="you@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              autoFocus
              disabled={isSubmitting}
            />
          </div>

          {/* Password Field */}
          <div className="form-group">
            <label htmlFor="login-password" className="form-label">
              Password
            </label>
            <div className="password-input-wrapper">
              <input
                id="login-password"
                type={showPassword ? 'text' : 'password'}
                className="input-field"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                disabled={isSubmitting}
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                tabIndex={-1}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24" />
                    <line x1="1" y1="1" x2="23" y2="23" />
                  </svg>
                ) : (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                )}
              </button>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            className="btn-primary auth-submit-btn"
            disabled={isSubmitting || !email || !password}
            id="login-submit"
          >
            {isSubmitting ? (
              <>
                <div className="btn-spinner" />
                Signing in...
              </>
            ) : (
              'Sign in'
            )}
          </button>
        </form>

        {/* Register Link */}
        <p className="auth-switch-text">
          Don't have an account?{' '}
          <Link to="/register" className="auth-switch-link">
            Create one
          </Link>
        </p>
      </div>
    </div>
  )
}

export default LoginPage
