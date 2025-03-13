import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import pinia from './store'

// Import CSS
import './assets/main.css'

// Create and mount the Vue application
const app = createApp(App)
app.use(pinia)
app.use(router)

// Add global error handler
app.config.errorHandler = (err, vm, info) => {
  console.error('Vue Error:', err)
  console.error('Component:', vm)
  console.error('Error Info:', info)
}

// Mount the app
app.mount('#app') 