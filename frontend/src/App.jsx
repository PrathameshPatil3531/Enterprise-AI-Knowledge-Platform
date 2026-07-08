/**
 * App.jsx — Root Application Component
 *
 * Responsibilities:
 * - Wrap the entire app in BrowserRouter (React Router)
 * - Wrap in global state providers (added in future milestones)
 * - Render the AppRouter which defines all page routes
 */

import { BrowserRouter } from 'react-router-dom'
import AppRouter from './router/AppRouter'

function App() {
  return (
    <BrowserRouter>
      <AppRouter />
    </BrowserRouter>
  )
}

export default App
