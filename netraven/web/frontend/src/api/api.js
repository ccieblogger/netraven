import axios from 'axios'

// Safely access environment variables with fallbacks
const getEnvVariable = (key, defaultValue) => {
  // Check if import.meta.env exists (in Vite) and contains the key
  if (import.meta && import.meta.env && import.meta.env[key]) {
    return import.meta.env[key];
  }
  // Check if process.env exists (in Node.js) and contains the key
  if (typeof process !== 'undefined' && process.env && process.env[key]) {
    return process.env[key];
  }
  // Return default value if the environment variable is not found
  return defaultValue;
};

// Determine the API URL based on the current environment
let browserApiUrl = '';

// Get API base URL from environment variables with fallback
const envApiBaseUrl = getEnvVariable('VITE_API_BASE_URL', null);

// Detect WSL/remote environments by checking for hostname patterns
const isWsl = window.location.hostname.includes('ubuntu') || 
              window.location.hostname.includes('wsl') || 
              window.location.hostname.includes('debian');

console.log('API Configuration:')
console.log('Browser origin:', window.location.origin)
console.log('Browser hostname:', window.location.hostname)
console.log('Is WSL environment:', isWsl)
console.log('Environment API URL:', envApiBaseUrl)

// Determine the best API URL to use
if (envApiBaseUrl) {
  // Use environment variable if available
  browserApiUrl = envApiBaseUrl;
  console.log('Using environment variable API URL');
} else if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
  // Local development - frontend port 8080, API port 8000
  browserApiUrl = 'http://localhost:8000';
  console.log('Using local development API URL');
} else if (isWsl) {
  // WSL environment - use localhost with port 8000
  browserApiUrl = 'http://localhost:8000';
  console.log('Using WSL localhost API URL');
} else {
  // Production/Docker environment
  // If we're accessing the frontend from outside Docker via 8080 port
  // we need to construct the API URL using the same hostname but port 8000
  const currentOrigin = window.location.origin;
  const apiOrigin = currentOrigin.replace(':8080', ':8000');
  browserApiUrl = apiOrigin;
  console.log('Using dynamic API URL based on frontend origin');
}

console.log('Final API URL:', browserApiUrl)

// For direct container-to-container communication within Docker
// This overrides the browser URL for server-side API calls that happen within Docker
const internalApiUrl = 'http://netraven-api-1:8000';

const api = axios.create({
  baseURL: browserApiUrl,
  headers: {
    'Content-Type': 'application/json'
  },
  // Add important options for cross-origin requests
  withCredentials: false,
  timeout: 15000 // 15 seconds timeout
})

// Add request interceptor to attach the authentication token
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    console.log('API Request:', {
      url: config.url,
      method: config.method,
      baseURL: config.baseURL,
      fullURL: config.baseURL + config.url,
      hasToken: !!token
    })
    return config
  },
  error => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Add response interceptor to handle token expiration
api.interceptors.response.use(
  response => {
    console.log('API Response:', {
      url: response.config.url,
      status: response.status,
      data: response.data
    })
    return response
  },
  error => {
    console.error('API Response Error:', {
      url: error.config?.url,
      status: error.response?.status,
      data: error.response?.data,
      message: error.message
    })
    if (error.response && error.response.status === 401) {
      // Token expired or invalid, redirect to login
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth service
export const authService = {
  async login(username, password) {
    console.log('Auth Service: Login attempt for user:', username)
    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)
    
    try {
      // Try multiple API URLs if needed for troubleshooting
      let loginUrl = browserApiUrl + '/api/auth/token';
      console.log('Making login request to:', loginUrl);
      
      const response = await fetch(loginUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: formData,
        mode: 'cors'
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('Auth Service: Login response not OK', response.status, errorData);
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorData.detail || 'Unknown error'}`);
      }
      
      const data = await response.json();
      console.log('Auth Service: Login successful, token received', data);
      
      // Store the token
      localStorage.setItem('access_token', data.access_token);
      return data;
    } catch (error) {
      console.error('Auth Service: Login failed', error);
      
      // If the first attempt failed, try with a fallback URL directly
      if (error.message.includes('NetworkError') || error.message.includes('Failed to fetch')) {
        try {
          console.log('Auth Service: First login attempt failed, trying fallback URL');
          const fallbackUrl = 'http://localhost:8000/api/auth/token';
          console.log('Making fallback login request to:', fallbackUrl);
          
          const fallbackResponse = await fetch(fallbackUrl, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: formData,
            mode: 'cors'
          });
          
          if (!fallbackResponse.ok) {
            const errorData = await fallbackResponse.json().catch(() => ({}));
            console.error('Auth Service: Fallback login response not OK', fallbackResponse.status, errorData);
            throw new Error(`HTTP error! status: ${fallbackResponse.status}, message: ${errorData.detail || 'Unknown error'}`);
          }
          
          const data = await fallbackResponse.json();
          console.log('Auth Service: Fallback login successful, token received', data);
          
          // Store the token
          localStorage.setItem('access_token', data.access_token);
          return data;
        } catch (fallbackError) {
          console.error('Auth Service: Fallback login failed', fallbackError);
          throw fallbackError;
        }
      }
      
      throw error;
    }
  },
  
  async getCurrentUser() {
    console.log('Auth Service: Fetching current user')
    try {
      const response = await api.get('/api/auth/users/me')
      console.log('Auth Service: User data received', response.data)
      return response.data
    } catch (error) {
      console.error('Auth Service: Failed to fetch user', error)
      throw error
    }
  },
  
  logout() {
    console.log('Auth Service: Logging out')
    localStorage.removeItem('access_token')
  }
}

// Devices service
export const deviceService = {
  async getDevices() {
    const response = await api.get('/api/devices')
    return response.data
  },
  
  async getDevice(id) {
    const response = await api.get(`/api/devices/${id}`)
    return response.data
  },
  
  async createDevice(deviceData) {
    console.log('API: Creating device with data:', deviceData)
    const response = await api.post('/api/devices', deviceData)
    console.log('API: Device creation response:', response.data)
    return response.data
  },
  
  async updateDevice(id, deviceData) {
    console.log('API: Updating device with data:', deviceData)
    const response = await api.put(`/api/devices/${id}`, deviceData)
    console.log('API: Device update response:', response.data)
    return response.data
  },
  
  async deleteDevice(id) {
    const response = await api.delete(`/api/devices/${id}`)
    return response.data
  },
  
  async backupDevice(id) {
    const response = await api.post(`/api/devices/${id}/backup`)
    return response.data
  }
}

// Backups service
export const backupService = {
  async getBackups(params = {}) {
    const response = await api.get('/api/backups', { params })
    return response.data
  },
  
  async getBackup(id) {
    const response = await api.get(`/api/backups/${id}`)
    return response.data
  },
  
  async getBackupContent(id) {
    const response = await api.get(`/api/backups/${id}/content`)
    return response.data
  },
  
  async compareBackups(backup1Id, backup2Id) {
    const response = await api.post('/api/backups/compare', {
      backup1_id: backup1Id,
      backup2_id: backup2Id
    })
    return response.data
  },
  
  async restoreBackup(id) {
    const response = await api.post(`/api/backups/${id}/restore`)
    return response.data
  },
  
  async deleteBackup(id) {
    const response = await api.delete(`/api/backups/${id}`)
    return response.data
  }
}

export default api 