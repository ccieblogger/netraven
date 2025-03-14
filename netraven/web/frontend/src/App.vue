<template>
  <div id="app">
    <!-- Simple error display -->
    <div v-if="appError" class="app-error">
      <div class="error-container">
        <h2>Application Error</h2>
        <p>{{ appError }}</p>
        <div class="error-actions">
          <button @click="reloadApp" class="error-button">Reload Application</button>
        </div>
      </div>
    </div>
    
    <!-- Simple loading indicator -->
    <div v-if="isInitializing" class="app-loading">
      <div class="loading-container">
        <div class="spinner"></div>
        <p>Loading application...</p>
      </div>
    </div>
    
    <!-- Main application -->
    <router-view v-if="!appError && !isInitializing" />
  </div>
</template>

<script>
import { ref, onErrorCaptured, onMounted } from 'vue'

export default {
  name: 'App',
  
  setup() {
    const appError = ref(null)
    const isInitializing = ref(true)
    
    // Simple error handler
    onErrorCaptured((err, instance, info) => {
      console.error('App Error:', err)
      
      // Show errors in the UI
      appError.value = `${err.message || 'Unknown error'}`
      
      // Don't propagate app-level errors
      return instance && instance.$options && 
             ['App'].includes(instance.$options.name) 
        ? false 
        : true;
    })
    
    // Simple initialization
    onMounted(() => {
      console.log('App: Component mounted, initializing...')
      
      // Brief delay to ensure CSS and resources are loaded
      setTimeout(() => {
        isInitializing.value = false
      }, 200)
    })
    
    // Reload the application
    const reloadApp = () => {
      window.location.reload()
    }
    
    return {
      appError,
      isInitializing,
      reloadApp
    }
  }
}
</script>

<style>
@import 'tailwindcss/base';
@import 'tailwindcss/components';
@import 'tailwindcss/utilities';

body {
  background-color: #f3f4f6;
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
    Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

.app-error {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.app-loading {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9998;
}

.loading-container {
  text-align: center;
}

.spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border-left-color: #3b82f6;
  margin: 0 auto 1rem;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-container {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  padding: 2rem;
  max-width: 500px;
  width: 90%;
  text-align: center;
}

.error-container h2 {
  color: #ef4444;
  margin-top: 0;
}

.error-actions {
  margin-top: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.error-button {
  background-color: #3b82f6;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.25rem;
  cursor: pointer;
  font-size: 1rem;
}

.error-button:hover {
  background-color: #2563eb;
}
</style> 