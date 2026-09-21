import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api/8090': {
        target: 'http://localhost:8090',
        rewrite: (path) => path.replace(/^\/api\/8090/, ''),
        changeOrigin: true,
      },
      '/api/8002': {
        target: 'http://localhost:8002',
        rewrite: (path) => path.replace(/^\/api\/8002/, ''),
        changeOrigin: true,
      },
      '/api/8085': {
        target: 'http://localhost:8085',
        rewrite: (path) => path.replace(/^\/api\/8085/, ''),
        changeOrigin: true,
      },
      '/api/8080': {
        target: 'http://localhost:8085',
        rewrite: (path) => path.replace(/^\/api\/8080/, ''),
        changeOrigin: true,
      },
      '/api/8004': {
        target: 'http://localhost:8004',
        rewrite: (path) => path.replace(/^\/api\/8004/, ''),
        changeOrigin: true,
      },
      // Route remaining /api/* requests to the serve_dashboard.py proxy on port 9000
      '/api': {
        target: 'http://localhost:9000',
        changeOrigin: true,
      },
    },
  },
})
