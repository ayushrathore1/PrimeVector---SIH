import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3000,
    host: true,
    proxy: {
      // Dynamic proxy: /api/{port}/path → http://localhost:{port}/path
      // Covers all 8 microservices:
      //   8000 risk-fusion-engine
      //   8001 feature-extraction-service
      //   8002 spoof-detection-service
      //   8003 enrollment-service
      //   8004 policy-threshold-engine
      //   8005 alerting-service
      //   8080 orchestrator
      '/api': {
        target: 'http://localhost',
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on('proxyReq', (proxyReq, req) => {
            // Extract port from /api/{port}/... and rewrite
            const match = req.url?.match(/^\/api\/(\d+)(\/.*)?$/);
            if (match) {
              const port = match[1];
              const path = match[2] || '/';
              proxyReq.path = path;
              proxyReq.setHeader('host', `localhost:${port}`);
            }
          });
        },
        router: (req) => {
          const match = req.url?.match(/^\/api\/(\d+)/);
          if (match) {
            return `http://localhost:${match[1]}`;
          }
          return 'http://localhost:8080';
        },
        rewrite: (path) => path.replace(/^\/api\/\d+/, ''),
      },
    },
  },
});
