import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import postcssConfig from './postcss.config.js'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  css: {
    devSourcemap: true,
  },
  server: {
    host: '0.0.0.0', // Listen on all interfaces to be accessible from Nginx
    port: 5173,
    strictPort: true, // Fail if port is already in use
    proxy: {
      // Proxy API requests to backend - do NOT rewrite the path, preserve /api for FastAPI/Nginx compatibility
      '/api': {
        target: 'http://api:8000',
        changeOrigin: true,
        secure: false,
        // Remove the rewrite so /api prefix is preserved
        // rewrite: (path) => path.replace(/^\/api/, ''),
        configure: (proxy) => {
          proxy.on('proxyReq', (proxyReq, req) => {
            // Log the proxied URL for debugging
            console.log(`Proxying request to: ${req.url}`);
          });
        }
      }
    },
    hmr: {
      // HMR settings for working behind Nginx
      clientPort: 80, // Port the browser will connect to
      path: '/@vite/client', // WebSocket endpoint path
      timeout: 120000, // Increase timeout for reconnection attempts
    },
    watch: {
      usePolling: true, // Needed for some environments
      interval: 1000
    }
  },
  optimizeDeps: {
    // Cleaned up: no ajv-related packages needed
  }
})
