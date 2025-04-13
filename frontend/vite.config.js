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
    host: 'localhost', // Change from '0.0.0.0' to 'localhost'
    port: 5173,
    strictPort: true, // Fail if port is already in use
    hmr: {
      host: 'localhost', // Ensure HMR uses 'localhost'
      port: 5173,
      protocol: 'ws',
      clientPort: 5173,
      overlay: false
    },
    watch: {
      usePolling: true, // Needed for some environments
      interval: 1000
    },
    // Add proxy configuration for API requests
    proxy: {
      '/api': {
        target: 'http://api:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
