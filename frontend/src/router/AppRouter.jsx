/**
 * AppRouter.jsx — Application Route Definitions
 *
 * Defines all routes and their protection status.
 *
 * Route types:
 * - Guest routes: Only accessible when NOT authenticated (Login, Register)
 * - Protected routes: Require valid JWT (Dashboard, Documents, Chat)
 *
 * Authentication and route protection are handled by:
 * - ProtectedRoute: Redirects to /login if not authenticated
 * - GuestRoute: Redirects to /dashboard if already authenticated
 */

import { Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute from '../components/ProtectedRoute'
import GuestRoute from '../components/GuestRoute'
import LoginPage from '../pages/LoginPage'
import RegisterPage from '../pages/RegisterPage'

// --- Placeholder pages (replaced with real implementations in future milestones) ---
const Placeholder = ({ title }) => (
  <div className="min-h-screen flex items-center justify-center bg-slate-900">
    <div className="card text-center max-w-md w-full mx-4">
      <div className="text-4xl mb-4">🚀</div>
      <h1 className="text-2xl font-bold text-slate-100 mb-2">{title}</h1>
      <p className="text-slate-400 text-sm">
        Enterprise AI Knowledge Platform
      </p>
      <p className="text-slate-500 text-xs mt-2">Coming in a future milestone</p>
    </div>
  </div>
)

function AppRouter() {
  return (
    <Routes>
      {/* Guest routes — only accessible when NOT logged in */}
      <Route path="/login" element={
        <GuestRoute><LoginPage /></GuestRoute>
      } />
      <Route path="/register" element={
        <GuestRoute><RegisterPage /></GuestRoute>
      } />

      {/* Protected routes — require authentication */}
      <Route path="/dashboard" element={
        <ProtectedRoute><Placeholder title="Dashboard" /></ProtectedRoute>
      } />
      <Route path="/documents" element={
        <ProtectedRoute><Placeholder title="Documents" /></ProtectedRoute>
      } />
      <Route path="/chat" element={
        <ProtectedRoute><Placeholder title="Chat" /></ProtectedRoute>
      } />
      <Route path="/chat/:id" element={
        <ProtectedRoute><Placeholder title="Chat Session" /></ProtectedRoute>
      } />

      {/* Default redirect */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      {/* 404 fallback */}
      <Route path="*" element={<Placeholder title="Page Not Found" />} />
    </Routes>
  )
}

export default AppRouter
