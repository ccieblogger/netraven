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
  // Use localStorage directly to always get the latest token
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  
  // Restore /api prefix logic: prepend /api to all non-absolute URLs
  if (config.url && !config.url.startsWith('/api') && !config.url.match(/^https?:\/\//)) {
    config.url = `/api${config.url.startsWith('/') ? '' : '/'}${config.url}`;
  }
  
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

/**
 * Fetch the latest reachability job result for a device
 * @param {number} deviceId
 * @returns {Promise<Object|null>} Latest job result or null if not found
 */
export async function getLatestReachabilityJobResult(deviceId) {
  try {
    const res = await api.get(`/job-results/?device_id=${deviceId}&job_type=reachability&page=1&size=1`);
    if (res.data && Array.isArray(res.data.items) && res.data.items.length > 0) {
      return res.data.items[0];
    }
    return null;
  } catch (err) {
    console.error('Failed to fetch reachability job result:', err);
    return null;
  }
}

/**
 * Fetch available job types from the backend
 * @returns {Promise<Array>} List of job type objects
 */
export async function getJobTypes() {
  try {
    const res = await api.get('/jobs/job-types');
    return res.data;
  } catch (err) {
    console.error('Failed to fetch job types:', err);
    return [];
  }
}

export default api;
