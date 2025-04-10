import axios from 'axios';
import { useAuthStore } from '../store/auth';

// Determine API base URL from environment variables or use a default
// Ensure the backend service address is correct (e.g., localhost:8000 for local dev)
const API_BASE_URL = 'http://localhost:8000'; // Force to use localhost:8000

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // Optional: Set a request timeout (e.g., 10 seconds)
  withCredentials: true, // Add this to enable sending cookies with CORS requests
  headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
  }
});

// Request Interceptor: Add JWT token to Authorization header
api.interceptors.request.use((config) => {
  const authStore = useAuthStore(); // Get store instance inside interceptor
  const token = authStore.token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  // Handle request error
  console.error('Axios Request Error:', error);
  return Promise.reject(error);
});

// Response Interceptor (Optional): Handle common responses/errors globally
api.interceptors.response.use(
  (response) => {
    // Any status code that lie within the range of 2xx cause this function to trigger
    // Do something with response data
    return response;
  },
  (error) => {
    // Any status codes that falls outside the range of 2xx cause this function to trigger
    console.error('Axios Response Error:', error.response || error.message);
    const authStore = useAuthStore();

    if (error.response) {
        // Handle specific status codes (e.g., 401 Unauthorized)
        if (error.response.status === 401) {
            console.error('Unauthorized access - 401. Logging out.');
            // Token might be invalid or expired, attempt logout
            authStore.logout();
            // Optionally redirect to login page
            // window.location.href = '/login'; 
        }
        // Handle other error statuses (403 Forbidden, 404 Not Found, 500 Server Error etc.)

    } else if (error.request) {
        // The request was made but no response was received
        console.error('Network Error: No response received from server.');
        // Handle network errors (e.g., show a notification)
    } else {
        // Something happened in setting up the request that triggered an Error
        console.error('Axios Error', error.message);
    }
    
    // Do something with response error
    return Promise.reject(error);
  }
);

export default api;
