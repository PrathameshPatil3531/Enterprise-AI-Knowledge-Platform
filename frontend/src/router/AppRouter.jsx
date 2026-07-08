/**
 * AppRouter.jsx — Application Route Definitions
 *
 * Defines all routes and their protection status.
 *
 * Route types:
 * - Public routes: Accessible without authentication (Login, Register)
 * - Protected routes: Require valid JWT (Dashboard, Documents, Chat)
 *
 * Currently all routes render placeholder pages (Milestone 1 scope).
 * Authentication and protected route guards are added in Milestone 2.
 */

import { Routes, Route, Navigate } from 'react-router-dom'

// --- Placeholder pages (replaced with real implementations in future milestones) ---
const Placeholder = ({ title }) => (
  <div className="min-h-screen flex items-center justify-center bg-slate-900">
    <div className="card text-center max-w-md w-full mx-4">
      <div className="text-4xl mb-4">🚀</div>
      <h1 className="text-2xl font-bold text-slate-100 mb-2">{title}</h1>
      <p className="text-slate-400 text-sm">
        Enterprise AI Knowledge Platform
      </p>
      <p className="text-slate-500 text-xs mt-2">Milestone 1 — Infrastructure Ready</p>
    </div>
  </div>
)

function AppRouter() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login"    element={<Placeholder title="Login" />} />
      <Route path="/register" element={<Placeholder title="Register" />} />

      {/* Protected routes (auth guard added in Milestone 2) */}
      <Route path="/dashboard" element={<Placeholder title="Dashboard" />} />
      <Route path="/documents" element={<Placeholder title="Documents" />} />
      <Route path="/chat"      element={<Placeholder title="Chat" />} />
      <Route path="/chat/:id"  element={<Placeholder title="Chat Session" />} />

      {/* Default redirect */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      {/* 404 fallback */}
      <Route path="*" element={<Placeholder title="Page Not Found" />} />
    </Routes>
  )
}

export default AppRouter
