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

// Ensure we always have a fallback URL if nothing else worked
if (!browserApiUrl) {
  browserApiUrl = 'http://localhost:8000';
  console.log('Falling back to default API URL: http://localhost:8000');
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
      // Token expired or invalid - clear the token but don't redirect
      // This prevents automatic redirects that might interfere with Vue Router
      console.log('API: Token invalid (401), clearing token but not redirecting')
      localStorage.removeItem('access_token')
      
      // Only redirect to login if not already on login page
      // This prevents redirect loops
      if (!window.location.pathname.includes('/login')) {
        console.log('API: Not on login page, router will handle redirection')
        // We'll let the Vue Router handle this redirection now
      }
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
    
    // Try multiple login approaches in sequence for better reliability
    const loginUrlOptions = [
      browserApiUrl + '/api/auth/token',
      'http://localhost:8000/api/auth/token', 
      window.location.hostname + ':8000/api/auth/token',
      'http://' + window.location.hostname + ':8000/api/auth/token'
    ];
    
    let lastError = null;
    
    // Try each URL in sequence until one works
    for (const loginUrl of loginUrlOptions) {
      try {
        console.log('Auth Service: Attempting login with URL:', loginUrl);
        
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
        console.error(`Auth Service: Login attempt failed for URL ${loginUrl}:`, error);
        lastError = error;
        // Continue to the next URL option
      }
    }
    
    // If we get here, all login attempts failed
    console.error('Auth Service: All login attempts failed');
    throw lastError || new Error('Failed to connect to the API server. Please check your network connection.');
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

// Tag service
export const tagService = {
  async getTags(params = {}) {
    console.log('Tag Service: Fetching all tags', params)
    const response = await api.get('/api/tags', { params })
    return response.data
  },
  
  async getTag(id) {
    console.log('Tag Service: Fetching tag', id)
    const response = await api.get(`/api/tags/${id}`)
    return response.data
  },
  
  async createTag(tagData) {
    console.log('Tag Service: Creating tag', tagData)
    const response = await api.post('/api/tags', tagData)
    return response.data
  },
  
  async updateTag(id, tagData) {
    console.log('Tag Service: Updating tag', id, tagData)
    const response = await api.put(`/api/tags/${id}`, tagData)
    return response.data
  },
  
  async deleteTag(id) {
    console.log('Tag Service: Deleting tag', id)
    await api.delete(`/api/tags/${id}`)
    return true
  },
  
  async getDevicesForTag(id, params = {}) {
    console.log('Tag Service: Fetching devices for tag', id, params)
    const response = await api.get(`/api/tags/${id}/devices`, { params })
    return response.data
  },
  
  async assignTagsToDevices(deviceIds, tagIds) {
    console.log('=== API DEBUG: assignTagsToDevices ===');
    console.log('Method called with params:', { deviceIds, tagIds });
    console.log('deviceIds type:', Array.isArray(deviceIds) ? 'array' : typeof deviceIds);
    console.log('tagIds type:', Array.isArray(tagIds) ? 'array' : typeof tagIds);
    console.log('API URL:', `/api/tags/assign`);
    console.log('Request body:', {
      device_ids: deviceIds,
      tag_ids: tagIds
    });
    
    try {
      console.log('Making API request...');
      const response = await api.post('/api/tags/assign', {
        device_ids: deviceIds,
        tag_ids: tagIds
      });
      
      console.log('API response status:', response.status);
      console.log('API response data:', response.data);
      console.log('=== END API DEBUG ===');
      
      return response.data;
    } catch (error) {
      console.error('=== API ERROR ===');
      console.error('Error in assignTagsToDevices:', error);
      console.error('Error response:', error.response?.data);
      console.error('Error status:', error.response?.status);
      console.error('=== END API ERROR ===');
      throw error;
    }
  },
  
  async removeTagsFromDevices(deviceIds, tagIds) {
    console.log('=== API DEBUG: removeTagsFromDevices ===');
    console.log('Method called with params:', { deviceIds, tagIds });
    console.log('deviceIds type:', Array.isArray(deviceIds) ? 'array' : typeof deviceIds);
    console.log('tagIds type:', Array.isArray(tagIds) ? 'array' : typeof tagIds);
    
    try {
      console.log('Making API request...');
      const response = await api.post('/api/tags/unassign', {
        device_ids: deviceIds,
        tag_ids: tagIds
      });
      
      console.log('API response status:', response.status);
      console.log('API response data:', response.data);
      console.log('=== END API DEBUG ===');
      
      return response.data;
    } catch (error) {
      console.error('=== API ERROR ===');
      console.error('Error in removeTagsFromDevices:', error);
      console.error('Error response:', error.response?.data);
      console.error('Error status:', error.response?.status);
      console.error('=== END API ERROR ===');
      throw error;
    }
  }
}

// Tag Rules service
export const tagRuleService = {
  async getTagRules(params = {}) {
    console.log('Tag Rule Service: Fetching all tag rules', params)
    const response = await api.get('/api/tag-rules', { params })
    return response.data
  },
  
  async getTagRule(id) {
    console.log('Tag Rule Service: Fetching tag rule', id)
    const response = await api.get(`/api/tag-rules/${id}`)
    return response.data
  },
  
  async createTagRule(ruleData) {
    console.log('Tag Rule Service: Creating tag rule', ruleData)
    const response = await api.post('/api/tag-rules', ruleData)
    return response.data
  },
  
  async updateTagRule(id, ruleData) {
    console.log('Tag Rule Service: Updating tag rule', id, ruleData)
    const response = await api.put(`/api/tag-rules/${id}`, ruleData)
    return response.data
  },
  
  async deleteTagRule(id) {
    console.log('Tag Rule Service: Deleting tag rule', id)
    await api.delete(`/api/tag-rules/${id}`)
    return true
  },
  
  async applyTagRule(id) {
    console.log('Tag Rule Service: Applying tag rule', id)
    const response = await api.post(`/api/tag-rules/${id}/apply`)
    return response.data
  },
  
  async testRule(ruleCriteria) {
    console.log('Tag Rule Service: Testing rule criteria', ruleCriteria)
    const response = await api.post('/api/tag-rules/test', {
      rule_criteria: ruleCriteria
    })
    return response.data
  }
}

export default api 