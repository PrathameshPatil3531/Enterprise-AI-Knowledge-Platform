/**
 * RegisterPage.jsx — User Registration Page
 *
 * Premium dark-mode registration with:
 * - Same visual style as LoginPage for consistency
 * - Email, full name, password, and confirm password fields
 * - Real-time password strength indicator
 * - Client-side validation matching backend rules
 * - Loading state on submit
 * - API error display
 * - Link to Login page
 */

import { useState, useMemo } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import useAuthStore from '../store/authStore'

/**
 * Validate password against the same rules as the backend:
 * - Minimum 8 characters
 * - At least one uppercase letter
 * - At least one lowercase letter
 * - At least one digit
 *
 * Returns an array of { label, met } objects for the strength indicator.
 */
function getPasswordChecks(password) {
  return [
    { label: '8+ characters', met: password.length >= 8 },
    { label: 'Uppercase letter', met: /[A-Z]/.test(password) },
    { label: 'Lowercase letter', met: /[a-z]/.test(password) },
    { label: 'Number', met: /\d/.test(password) },
  ]
}

function RegisterPage() {
  const navigate = useNavigate()
  const register = useAuthStore((s) => s.register)
  const clearError = useAuthStore((s) => s.clearError)
  const storeError = useAuthStore((s) => s.error)

  const [email, setEmail] = useState('')
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

  // Client-side validation
  const passwordChecks = useMemo(() => getPasswordChecks(password), [password])
  const allChecksPassed = passwordChecks.every((c) => c.met)
  const passwordsMatch = password === confirmPassword
  const metCount = passwordChecks.filter((c) => c.met).length

  // Determine strength level for the progress bar
  const strengthLevel = metCount === 0 ? 'none' : metCount <= 2 ? 'weak' : metCount <= 3 ? 'fair' : 'strong'
  const strengthColors = {
    none: 'bg-slate-600',
    weak: 'bg-red-500',
    fair: 'bg-amber-500',
    strong: 'bg-emerald-500',
  }
  const strengthLabels = {
    none: '',
    weak: 'Weak',
    fair: 'Fair',
    strong: 'Strong',
  }

  const canSubmit = email && password && confirmPassword && allChecksPassed && passwordsMatch && !isSubmitting

  const handleSubmit = async (e) => {
    e.preventDefault()
    clearError()

    if (!passwordsMatch) return
    if (!allChecksPassed) return

    setIsSubmitting(true)

    try {
      await register({
        email,
        password,
        full_name: fullName || undefined,
      })
      // Redirect to login with success message
      navigate('/login', {
        replace: true,
        state: { message: 'Account created successfully! Please sign in.' },
      })
    } catch {
      // Error is set in the store by the register action
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
              <rect width="40" height="40" rx="12" fill="url(#logo-gradient-reg)" />
              <path d="M12 28L20 12L28 28H12Z" fill="white" fillOpacity="0.9" />
              <path d="M16 24L20 16L24 24H16Z" fill="url(#logo-gradient-reg)" fillOpacity="0.5" />
              <defs>
                <linearGradient id="logo-gradient-reg" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#4f6ef7" />
                  <stop offset="1" stopColor="#8b5cf6" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <h1 className="auth-title">Create your account</h1>
          <p className="auth-subtitle">
            Get started with the AI Knowledge Platform
          </p>
        </div>

        {/* Error message */}
        {storeError && (
          <div className="auth-error-message">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 1C4.13 1 1 4.13 1 8s3.13 7 7 7 7-3.13 7-7S11.87 1 8 1zm-.5 3h1v5h-1V4zm.5 8a.75.75 0 110-1.5.75.75 0 010 1.5z" fill="#f87171" />
            </svg>
            {storeError}
          </div>
        )}

        {/* Register Form */}
        <form onSubmit={handleSubmit} className="auth-form" id="register-form">
          {/* Email Field */}
          <div className="form-group">
            <label htmlFor="register-email" className="form-label">
              Email address
            </label>
            <input
              id="register-email"
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

          {/* Full Name Field */}
          <div className="form-group">
            <label htmlFor="register-fullname" className="form-label">
              Full name <span className="text-slate-500 text-xs">(optional)</span>
            </label>
            <input
              id="register-fullname"
              type="text"
              className="input-field"
              placeholder="John Doe"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              autoComplete="name"
              disabled={isSubmitting}
              maxLength={255}
            />
          </div>

          {/* Password Field */}
          <div className="form-group">
            <label htmlFor="register-password" className="form-label">
              Password
            </label>
            <div className="password-input-wrapper">
              <input
                id="register-password"
                type={showPassword ? 'text' : 'password'}
                className="input-field"
                placeholder="Create a strong password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="new-password"
                disabled={isSubmitting}
                maxLength={128}
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

            {/* Password Strength Indicator */}
            {password.length > 0 && (
              <div className="password-strength">
                <div className="password-strength-bar">
                  <div
                    className={`password-strength-fill ${strengthColors[strengthLevel]}`}
                    style={{ width: `${(metCount / 4) * 100}%` }}
                  />
                </div>
                {strengthLabels[strengthLevel] && (
                  <span className={`password-strength-label ${
                    strengthLevel === 'strong' ? 'text-emerald-400' :
                    strengthLevel === 'fair' ? 'text-amber-400' : 'text-red-400'
                  }`}>
                    {strengthLabels[strengthLevel]}
                  </span>
                )}
              </div>
            )}

            {/* Password Requirements Checklist */}
            {password.length > 0 && (
              <ul className="password-checks">
                {passwordChecks.map((check) => (
                  <li
                    key={check.label}
                    className={`password-check-item ${check.met ? 'check-met' : 'check-unmet'}`}
                  >
                    {check.met ? (
                      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                        <path d="M3.5 7L6 9.5L10.5 4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    ) : (
                      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                        <circle cx="7" cy="7" r="2.5" stroke="currentColor" strokeWidth="1.5" />
                      </svg>
                    )}
                    {check.label}
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Confirm Password Field */}
          <div className="form-group">
            <label htmlFor="register-confirm-password" className="form-label">
              Confirm password
            </label>
            <div className="password-input-wrapper">
              <input
                id="register-confirm-password"
                type={showConfirmPassword ? 'text' : 'password'}
                className="input-field"
                placeholder="Re-enter your password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                autoComplete="new-password"
                disabled={isSubmitting}
                maxLength={128}
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                tabIndex={-1}
                aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
              >
                {showConfirmPassword ? (
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
            {confirmPassword && !passwordsMatch && (
              <p className="form-error-text">Passwords do not match</p>
            )}
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            className="btn-primary auth-submit-btn"
            disabled={!canSubmit}
            id="register-submit"
          >
            {isSubmitting ? (
              <>
                <div className="btn-spinner" />
                Creating account...
              </>
            ) : (
              'Create account'
            )}
          </button>
        </form>

        {/* Login Link */}
        <p className="auth-switch-text">
          Already have an account?{' '}
          <Link to="/login" className="auth-switch-link">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}

export default RegisterPage
