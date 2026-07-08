import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

/**
 * Vite Configuration
 *
 * WHY Vite?
 * - Native ES modules: no bundling during development → instant server start
 * - HMR (Hot Module Replacement): updates only the changed module, not the whole page
 * - Optimized production builds via Rollup
 * - 10-100x faster than Webpack for development
 *
 * @see https://vitejs.dev/config/
 */
export default defineConfig({
  plugins: [
    react(), // Enables React JSX transform + Fast Refresh (HMR for React)
  ],

  server: {
    port: 5173, // Default Vite port

    // API proxy: During development, forward /api requests to FastAPI
    // This avoids CORS issues when running frontend and backend on different ports
    // In production, Nginx handles this routing
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },

  build: {
    outDir: 'dist',        // Output directory for production build
    sourcemap: false,      // Disable sourcemaps in production (smaller bundle)
    minify: 'esbuild',     // esbuild minifier is 10-20x faster than terser
    rollupOptions: {
      output: {
        // Split vendor libraries into a separate chunk for better caching
        // Users' browsers cache react, react-dom separately from app code
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          axios: ['axios'],
        },
      },
    },
  },
})
