/**
 * main.jsx — React Application Bootstrap
 *
 * This is the entry point Vite uses (referenced in index.html).
 * It mounts the root React component into the DOM.
 *
 * WHY React.StrictMode?
 * - Enables additional runtime warnings in development
 * - Detects deprecated lifecycle methods
 * - Warns about unexpected side effects
 * - Has NO impact on production builds (automatically stripped)
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
