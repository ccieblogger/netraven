import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import pinia from './store'
import Toast from 'vue-toastification'
import 'vue-toastification/dist/index.css'
import axios from 'axios'

// Import CSS
import './assets/main.css'

// Router ready flag for initialization tracking
window.ROUTER_READY = false;

// Initialize error display flag
window.ROUTE_ERROR_DISPLAYED = false;

// Add global keyboard shortcut to show router errors
document.addEventListener('keydown', (event) => {
  // Ctrl+Shift+E to show error history
  if (event.ctrlKey && event.shiftKey && event.key === 'E') {
    try {
      const errorHistory = JSON.parse(localStorage.getItem('router_errors') || '[]');
      
      if (errorHistory.length === 0) {
        alert('No router errors have been captured yet.\n\nEnable error capture mode by adding ?capture=true to the URL.');
        return;
      }
      
      // Format the errors for display
      let errorMessage = '=== ROUTER ERROR HISTORY ===\n\n';
      
      errorHistory.forEach((error, index) => {
        errorMessage += `Error ${index + 1} (${new Date(error.timestamp).toLocaleTimeString()}):\n`;
        errorMessage += `Message: ${error.message}\n`;
        errorMessage += `URL: ${error.url}\n\n`;
      });
      
      errorMessage += 'Press F12 to open developer tools for more details.';
      
      alert(errorMessage);
    } catch (e) {
      console.error('Error displaying router error history:', e);
      alert('Error reading router error history: ' + e.message);
    }
  }
});

// Special handling for router initialization
router.isReady().then(() => {
  console.log('Router initialized successfully');
  window.ROUTER_READY = true;
}).catch(err => {
  console.error('Router initialization failed:', err);
  // If router fails to initialize, set a flag that the app can check
  window.ROUTER_INIT_ERROR = err.message;
  
  // Save to error history
  try {
    const errorRecord = {
      message: err.message,
      stack: err.stack,
      url: window.location.href,
      timestamp: new Date().toISOString(),
      source: 'router.isReady()'
    };
    
    const storedErrors = JSON.parse(localStorage.getItem('router_errors') || '[]');
    storedErrors.unshift(errorRecord);
    if (storedErrors.length > 5) storedErrors.pop();
    localStorage.setItem('router_errors', JSON.stringify(storedErrors));
  } catch (e) {
    console.error('Failed to save router initialization error:', e);
  }
});

// Initialize the app
const app = createApp(App)

// Add diagnostic API check
const apiUrl = process.env.VUE_APP_API_URL || 'http://localhost:8000'
const browserApiUrl = typeof window !== 'undefined' && window.location ? 
  `${window.location.protocol}//${window.location.host}` : apiUrl

// Configure axios default base URL
axios.defaults.baseURL = browserApiUrl;
console.log('Axios baseURL set to:', axios.defaults.baseURL);

console.log('Testing API connectivity...')
axios.get(`${browserApiUrl}/api/health`)
  .then(response => {
    console.log('API health check successful:', response.data)
    // Also check auth endpoints
    console.log('Checking auth endpoint URL:', `${browserApiUrl}/api/auth/token`)
  })
  .catch(error => {
    console.error('API health check failed:', error.message)
    if (error.response) {
      console.error('Error response:', error.response.status, error.response.data)
    } else if (error.request) {
      console.error('No response received from API')
    }
  })

app.use(pinia)
app.use(router)
app.use(Toast, {
  transition: "Vue-Toastification__bounce",
  maxToasts: 3,
  newestOnTop: true,
  position: "top-right",
  timeout: 5000,
  closeOnClick: true,
  pauseOnFocusLoss: true,
  pauseOnHover: true,
  draggable: true,
  draggablePercent: 0.6,
  showCloseButtonOnHover: false,
  hideProgressBar: false,
  closeButton: "button",
  icon: true,
  rtl: false
})

// Add global error handler
app.config.errorHandler = (err, vm, info) => {
  console.error('Vue Error:', err)
  console.error('Component:', vm?.$options?.name || 'Unknown')
  console.error('Error Info:', info)
  
  // Save serious errors to localStorage for debugging
  try {
    const errorRecord = {
      message: err.message,
      component: vm?.$options?.name || 'Unknown',
      info: info,
      url: window.location.href,
      timestamp: new Date().toISOString(),
      source: 'app.config.errorHandler'
    };
    
    const storedErrors = JSON.parse(localStorage.getItem('vue_errors') || '[]');
    storedErrors.unshift(errorRecord);
    if (storedErrors.length > 5) storedErrors.pop();
    localStorage.setItem('vue_errors', JSON.stringify(storedErrors));
  } catch (e) {
    console.error('Failed to save Vue error:', e);
  }
  
  // Special handling for navigation errors
  if (err.message && err.message.includes('location')) {
    console.warn('Global error handler caught location error');
    
    // Attempt to recover by redirecting to a safe route
    if (window.location.pathname !== '/login') {
      setTimeout(() => {
        window.location.href = '/login';
      }, 100);
    }
  }
}

// Mount the app
app.mount('#app') 