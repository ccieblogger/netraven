import axios from 'axios';
import { useAuthStore } from '../store/auth';

/**
 * API Service for NetRaven
 * 
 * This service creates an Axios instance configured for the NetRaven API.
 * With Nginx in place, we use a consistent /api prefix for all API requests.
 */

// Simple configuration with consistent base URL
const api = axios.create({
  baseURL: '', // Don't set a baseURL since we handle /api prefix in the interceptor
  timeout: 10000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// Request interceptor - Add authentication token
api.interceptors.request.use((config) => {
  // Add Auth token
  const authStore = useAuthStore();
  const token = authStore.token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  
  // Ensure proper URL formatting with '/api' prefix
  if (config.url && !config.url.startsWith('/api') && !config.url.match(/^https?:\/\//)) {
    // If URL doesn't have /api prefix and isn't absolute, prepend /api
    config.url = `/api${config.url.startsWith('/') ? '' : '/'}${config.url}`;
  }
  
  // Set the baseURL directly in the config to ensure it's used
  // This fixes issues where the baseURL wasn't being applied correctly
  config.baseURL = '';
  
  // Optional debug logging in development
  if (process.env.NODE_ENV === 'development') {
    console.log('API Request:', {
      method: config.method,
      url: config.url,
      fullPath: config.url
    });
  }
  
  return config;
}, (error) => {
  console.error('API Request Error:', error);
  return Promise.reject(error);
});

// Response interceptor - Handle common response scenarios
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle 401 Unauthorized globally
    if (error.response && error.response.status === 401) {
      const authStore = useAuthStore();
      console.warn('Authentication failed or token expired. Logging out.');
      authStore.logout();
    } 
    
    // Log network errors
    else if (error.request && !error.response) {
      console.error('Network Error: No response received from server.');
    }
    
    // Log other errors
    else {
      console.error('API Error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

export default api;
