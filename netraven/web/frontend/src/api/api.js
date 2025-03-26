import axios from 'axios'

// Configure axios defaults
axios.defaults.withCredentials = false;

// Add token refresh parameters
const TOKEN_REFRESH_THRESHOLD = 5 * 60 * 1000; // 5 minutes in milliseconds
const REFRESH_IN_PROGRESS = { status: false, promise: null };

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

// Get browserApiUrl based on environment
let browserApiUrl = process.env.VUE_APP_API_URL || 'http://localhost:8000';
console.log('INITIAL API URL:', browserApiUrl);

// In browser environments, use the browser's origin to ensure connectivity
if (typeof window !== 'undefined') {
  // If we're in the browser and the API URL has container references, use the browser's origin
  if (browserApiUrl.includes('api:8000') || browserApiUrl.includes('localhost:8000')) {
    const originalUrl = browserApiUrl;
    browserApiUrl = window.location.origin;
    console.log('TRANSFORMED API URL from', originalUrl, 'to', browserApiUrl);
  }
  console.log('USING API URL with browser origin:', browserApiUrl);
}

console.log('FINAL API URL:', browserApiUrl);

// Setup Axios interceptors for authentication handling
axios.interceptors.response.use(
  response => {
    // Pass through successful responses
    return response;
  },
  async error => {
    // Handle authentication errors
    if (error.response && error.response.status === 401) {
      console.warn('Authentication error intercepted:', error.response.data);
      
      const originalRequest = error.config;
      
      // Only try to refresh if it's an expired token and we're not already trying to refresh
      const isTokenExpired = error.response.data.detail === 'Token expired' || 
                             error.response.data.detail?.includes('Token has expired');
      
      // Don't retry if we've already tried to refresh for this request or if it's already the refresh endpoint
      const isRefreshEndpoint = originalRequest.url.includes('/api/auth/refresh');
      const hasBeenRetried = originalRequest._retry;

      if (isTokenExpired && !isRefreshEndpoint && !hasBeenRetried) {
        console.log('Token appears to be expired, attempting refresh');
        
        // Mark this request as retried to prevent infinite loops
        originalRequest._retry = true;
        
        try {
          // Try to refresh the token
          const apiClient = axios.API_CLIENT_INSTANCE;
          const newToken = await apiClient.refreshToken();
          
          if (newToken) {
            console.log('Token refreshed successfully, retrying original request');
            
            // Update the request with the new token
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            
            // Retry the original request with the new token
            return axios(originalRequest);
          }
        } catch (refreshError) {
          console.error('Failed to refresh token:', refreshError);
          // Let the error pass through to be handled by the components
        }
      } else if (isTokenExpired) {
        console.log('Token expired but cannot refresh: ' + 
                   (isRefreshEndpoint ? 'is refresh endpoint' : '') + 
                   (hasBeenRetried ? 'already retried' : ''));
      }
      
      // If we're here, either it's not an expired token issue, or refresh failed,
      // or it's the refresh endpoint itself that's failing
      
      // Only clear token if it's explicitly identified as invalid
      // We don't want to clear tokens for permission-based 401s
      const isInvalidToken = error.response.data.detail === 'Invalid token' || 
                            error.response.data.detail === 'Token expired' ||
                            error.response.data.detail === 'Could not validate credentials';
      
      if (isInvalidToken && localStorage.getItem('access_token')) {
        console.log('Clearing invalid token from localStorage due to 401 response');
        localStorage.removeItem('access_token');
      } else {
        console.log('Authentication error but token not cleared - may be a permissions issue');
      }
      
      // Add a flag to identify this as an auth error for components
      error.isAuthError = true;
    }
    
    return Promise.reject(error);
  }
);

// Add this function before the API client definition
const checkAuthHeader = () => {
  const token = localStorage.getItem('access_token');
  const hasAuthHeader = axios.defaults.headers.common['Authorization'] !== undefined;
  console.log('Auth check:', 
    token ? 'Token exists in localStorage' : 'No token in localStorage',
    hasAuthHeader ? 'Auth header set in axios' : 'No auth header in axios'
  );
  
  if (token && !hasAuthHeader) {
    console.log('Setting missing auth header from localStorage token');
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    return true;
  }
  return hasAuthHeader;
};

// Create API client
const apiClient = {
  // Get auth header for authenticated requests
  getAuthHeader() {
    const token = localStorage.getItem('access_token');
    
    if (!token) {
      console.warn('No authentication token available');
      return {};
    }
    
    // Validate basic token format
    if (typeof token !== 'string' || token.split('.').length !== 3) {
      console.error('Invalid token format in localStorage');
      
      // Clear invalid token
      localStorage.removeItem('access_token');
      return {};
    }
    
    try {
      // Check token expiration
      const payload = JSON.parse(atob(token.split('.')[1]));
      
      if (payload.exp) {
        const now = Math.floor(Date.now() / 1000);
        const expiresIn = payload.exp - now;
        
        // If token is expired, clear it
        if (now >= payload.exp) {
          console.warn('Token has expired, clearing from localStorage');
          localStorage.removeItem('access_token');
          return {};
        }
        
        // If token is close to expiration, trigger a refresh in the background
        if (expiresIn < TOKEN_REFRESH_THRESHOLD / 1000 && !REFRESH_IN_PROGRESS.status) {
          console.log(`Token expiring soon (${expiresIn}s), triggering background refresh`);
          this.refreshToken().catch(err => {
            console.error('Background token refresh failed:', err);
          });
        }
        
        // Log token scopes for debugging
        if (payload.scope) {
          console.log('Token scopes:', payload.scope);
          
          // Enhanced debugging for device operations
          const currentPath = window.location.pathname;
          if (currentPath.includes('/devices')) {
            const hasDevicePermission = payload.scope.includes('write:devices') || 
                                       payload.scope.includes('admin:*');
            console.log('Current path includes /devices, has device permission:', hasDevicePermission);
            
            if (!hasDevicePermission) {
              console.warn('Missing device management permission on devices page');
            }
          }
        } else {
          console.warn('Token payload does not contain scope information');
        }
      } else {
        console.warn('Token does not contain expiration information');
      }
    } catch (e) {
      console.error('Error validating token in getAuthHeader:', e);
      // Continue with token as is, don't clear it here to avoid potential valid tokens being removed
    }
    
    return token ? { Authorization: `Bearer ${token}` } : {};
  },

  // Token refresh method
  async refreshToken() {
    // If a refresh is already in progress, wait for it to complete rather than making a duplicate request
    if (REFRESH_IN_PROGRESS.status && REFRESH_IN_PROGRESS.promise) {
      console.log('Token refresh already in progress, waiting for it to complete');
      try {
        return await REFRESH_IN_PROGRESS.promise;
      } catch (err) {
        console.error('Waiting for in-progress token refresh failed:', err);
        throw err;
      }
    }
    
    // Get current token
    const currentToken = localStorage.getItem('access_token');
    if (!currentToken) {
      console.error('Cannot refresh token: No token available');
      return null;
    }
    
    // Set refresh in progress flag
    REFRESH_IN_PROGRESS.status = true;
    
    // Create a promise for the refresh operation
    REFRESH_IN_PROGRESS.promise = (async () => {
      try {
        console.log('Starting token refresh');
        
        // Call the token refresh API
        const response = await axios.post(`${browserApiUrl}/api/auth/refresh`, {}, {
          headers: {
            'Authorization': `Bearer ${currentToken}`,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          }
        });
        
        // Store the new token
        const newToken = response.data.access_token;
        
        if (newToken) {
          // Store the new token
          localStorage.setItem('access_token', newToken);
          console.log('Token refreshed successfully');
          
          // Decode and log new expiration time
          try {
            const payload = JSON.parse(atob(newToken.split('.')[1]));
            if (payload.exp) {
              const expiresAt = new Date(payload.exp * 1000);
              console.log(`New token expires at: ${expiresAt.toISOString()}`);
            }
          } catch (e) {
            console.error('Error parsing new token payload:', e);
          }
          
          return newToken;
        } else {
          console.error('Refresh token API returned success but no token');
          return null;
        }
      } catch (error) {
        console.error('Token refresh failed:', error);
        
        // If the refresh endpoint itself returns 401, the refresh token is probably invalid
        if (error.response && error.response.status === 401) {
          console.warn('Refresh token is invalid, clearing token');
          localStorage.removeItem('access_token');
        } else if (error.response && error.response.status === 400 && 
                  error.response.data.detail === 'Token is not near expiration yet') {
          // This is a normal case - token not close enough to expiration to refresh
          console.log('Token not near expiration yet, continuing with current token');
          return currentToken;
        }
        
        throw error;
      } finally {
        // Reset refresh in progress flag
        REFRESH_IN_PROGRESS.status = false;
        REFRESH_IN_PROGRESS.promise = null;
      }
    })();
    
    // Return the result of the refresh operation
    return REFRESH_IN_PROGRESS.promise;
  },

  // Authentication methods
  async login(username, password) {
    try {
      console.log('API: Attempting login with URL:', `${browserApiUrl}/api/auth/token`);
      const response = await axios.post(
        `${browserApiUrl}/api/auth/token`, 
        {
          username,
          password,
          grant_type: 'password'
        }, 
        {
          headers: { 'Content-Type': 'application/json' }
        }
      );
      
      if (response.data && response.data.access_token) {
        console.log('API: Login successful, received token');
        // Store token in localStorage
        localStorage.setItem('access_token', response.data.access_token);
        
        // Set authorization header for future requests
        axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
        console.log('API: Set Authorization header for future requests');
        
        // Return success object for compatibility with auth store
        return {
          success: true,
          data: response.data,
          message: 'Login successful'
        };
      } else {
        console.error('API: Login response missing access_token:', response.data);
        return {
          success: false,
          message: 'Invalid response from server'
        };
      }
    } catch (error) {
      console.error('Login error:', error);
      let errorMessage = 'Login failed';
      
      if (error.response) {
        // Server responded with error
        if (error.response.status === 401) {
          errorMessage = 'Invalid username or password';
        } else if (error.response.data && error.response.data.detail) {
          errorMessage = error.response.data.detail;
        } else if (error.response.data && error.response.data.message) {
          errorMessage = error.response.data.message;
        }
      } else if (error.request) {
        // Request made but no response
        errorMessage = 'Server not responding. Please try again later.';
      }
      
      return {
        success: false,
        message: errorMessage,
        error: error
      };
    }
  },

  async getCurrentUser() {
    try {
      const response = await axios.get(`${browserApiUrl}/api/users/me`, {
        headers: this.getAuthHeader()
      });
      return response.data;
    } catch (error) {
      console.error('Error getting current user:', error);
      
      // If we get a 401 Unauthorized, clear the token
      if (error.response && error.response.status === 401) {
        localStorage.removeItem('access_token');
      }
      
      throw error;
    }
  },

  logout() {
    // Remove token from localStorage
    localStorage.removeItem('access_token');
    
    // Remove authorization header
    delete axios.defaults.headers.common['Authorization'];
    
    try {
      // Attempt to revoke the token on the server (best effort)
      axios.post(`${browserApiUrl}/auth/revoke`)
        .catch(err => console.warn('Error revoking token during logout (continuing):', err));
    } catch (e) {
      console.warn('Error during token revocation (continuing):', e);
    }
    
    // Redirect is handled by the caller
    return {
      success: true,
      message: 'Logged out successfully'
    };
  },

  // Device methods
  async getDevices() {
    const response = await axios.get(`${browserApiUrl}/api/devices`, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  async getDevice(id) {
    const response = await axios.get(`${browserApiUrl}/api/devices/${id}`, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  // Enhanced device creation method with better error handling
  async createDevice(deviceData) {
    try {
      // Get authentication headers
      const headers = this.getAuthHeader();
      
      // Log authentication headers for debugging (safely removing sensitive data)
      if (headers.Authorization) {
        const authParts = headers.Authorization.split('.');
        console.log('Using authorization header with token parts count:', authParts.length);
        
        // Log token info if available
        if (authParts.length === 3) {
          try {
            const payload = JSON.parse(atob(authParts[1]));
            console.log('Token payload contains scopes:', !!payload.scope);
            console.log('Token subject:', payload.sub);
            
            // Check for device management permissions
            const hasDevicePermission = payload.scope && 
              (payload.scope.includes('write:devices') || 
               payload.scope.includes('admin:*'));
               
            console.log('Token has device management permission:', hasDevicePermission);
            
            if (!hasDevicePermission) {
              console.error('Token lacks necessary permissions for device management');
            }
          } catch (e) {
            console.error('Error parsing token payload:', e);
          }
        }
      } else {
        console.error('No Authorization header available for device creation');
      }
      
      // Make the API request
      console.log('Sending device creation request to:', `${browserApiUrl}/api/devices`);
      const response = await axios.post(`${browserApiUrl}/api/devices`, deviceData, {
        headers: headers
      });
      
      console.log('Device created successfully:', response.data);
      return response.data;
    } catch (error) {
      // Enhanced error logging for device creation
      console.error('Error in device creation:', error.message);
      
      if (error.response) {
        console.error('Error status:', error.response.status);
        console.error('Error details:', error.response.data);
        
        // Special handling for authentication errors
        if (error.response.status === 401) {
          console.error('Authentication error during device creation. Token may be invalid or insufficient permissions.');
          
          // Mark this as an authentication error
          error.isAuthError = true;
        }
      } else if (error.request) {
        console.error('No response received from server');
      }
      
      // Re-throw for component handling
      throw error;
    }
  },

  async updateDevice(id, deviceData) {
    const response = await axios.put(`${browserApiUrl}/api/devices/${id}`, deviceData, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  async deleteDevice(id) {
    const response = await axios.delete(`${browserApiUrl}/api/devices/${id}`, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  async backupDevice(id) {
    const response = await axios.post(`${browserApiUrl}/api/devices/${id}/backup`, {}, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  async checkDeviceReachability(id) {
    const response = await axios.post(`${browserApiUrl}/api/devices/${id}/reachability`, {}, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  // Backup methods
  async getBackups(params = {}) {
    const response = await axios.get(`${browserApiUrl}/api/backups`, {
      headers: this.getAuthHeader(),
      params
    });
    return response.data;
  },

  async getBackup(id) {
    const response = await axios.get(`${browserApiUrl}/api/backups/${id}`, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  async getBackupContent(id) {
    const response = await axios.get(`${browserApiUrl}/api/backups/${id}/content`, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  async compareBackups(backup1Id, backup2Id) {
    const response = await axios.get(`${browserApiUrl}/api/backups/compare`, {
      headers: this.getAuthHeader(),
      params: {
        backup1_id: backup1Id,
        backup2_id: backup2Id
      }
    });
    return response.data;
  },

  async restoreBackup(id) {
    const response = await axios.post(`${browserApiUrl}/api/backups/${id}/restore`, {}, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  async deleteBackup(id) {
    const response = await axios.delete(`${browserApiUrl}/api/backups/${id}`, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  // Tag methods
  async getTags(params = {}) {
    const response = await axios.get(`${browserApiUrl}/api/tags`, {
      headers: this.getAuthHeader(),
      params
    });
    return response.data;
  },

  async getTag(id) {
    const response = await axios.get(`${browserApiUrl}/api/tags/${id}`, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  async createTag(tagData) {
    const response = await axios.post(`${browserApiUrl}/api/tags`, tagData, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  async updateTag(id, tagData) {
    const response = await axios.put(`${browserApiUrl}/api/tags/${id}`, tagData, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  async deleteTag(id) {
    const response = await axios.delete(`${browserApiUrl}/api/tags/${id}`, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  async getDevicesForTag(id, params = {}) {
    const response = await axios.get(`${browserApiUrl}/api/tags/${id}/devices`, {
      headers: this.getAuthHeader(),
      params
    });
    return response.data;
  },

  async getTagsForDevice(deviceId) {
    const response = await axios.get(`${browserApiUrl}/api/tags/device/${deviceId}`, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  async assignTagsToDevices(deviceIds, tagIds) {
    const response = await axios.post(
      `${browserApiUrl}/api/tags/assign`,
      {
        device_ids: deviceIds,
        tag_ids: tagIds
      },
      {
        headers: this.getAuthHeader()
      }
    );
    return response.data;
  },

  async removeTagsFromDevices(deviceIds, tagIds) {
    const response = await axios.post(
      `${browserApiUrl}/api/tags/remove`,
      {
        device_ids: deviceIds,
        tag_ids: tagIds
      },
      {
        headers: this.getAuthHeader()
      }
    );
    return response.data;
  },

  // Tag rule methods
  async getTagRules(params = {}) {
    const response = await axios.get(`${browserApiUrl}/api/tag-rules`, {
      headers: this.getAuthHeader(),
      params
    });
    return response.data;
  },

  async getTagRule(id) {
    const response = await axios.get(`${browserApiUrl}/api/tag-rules/${id}`, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  async createTagRule(ruleData) {
    const response = await axios.post(`${browserApiUrl}/api/tag-rules`, ruleData, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  async updateTagRule(id, ruleData) {
    const response = await axios.put(`${browserApiUrl}/api/tag-rules/${id}`, ruleData, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  async deleteTagRule(id) {
    const response = await axios.delete(`${browserApiUrl}/api/tag-rules/${id}`, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  async applyTagRule(id) {
    const response = await axios.post(`${browserApiUrl}/api/tag-rules/${id}/apply`, {}, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  async testRule(ruleCriteria) {
    const response = await axios.post(`${browserApiUrl}/api/tag-rules/test`, ruleCriteria, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  // Job log methods
  async getJobLogs(params = {}) {
    const response = await axios.get(`${browserApiUrl}/api/job-logs`, {
      headers: this.getAuthHeader(),
      params
    });
    return response.data;
  },

  async getJobLog(id, includeEntries = false) {
    const response = await axios.get(`${browserApiUrl}/api/job-logs/${id}`, {
      headers: this.getAuthHeader(),
      params: { include_entries: includeEntries }
    });
    return response.data;
  },

  async getJobLogEntries(id, params = {}) {
    const response = await axios.get(`${browserApiUrl}/api/job-logs/${id}/entries`, {
      headers: this.getAuthHeader(),
      params
    });
    return response.data;
  },

  async deleteJobLog(id) {
    const response = await axios.delete(`${browserApiUrl}/api/job-logs/${id}`, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  async updateRetentionPolicy(policyData) {
    const response = await axios.put(`${browserApiUrl}/api/job-logs/retention`, policyData, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  async cleanupJobLogs(days) {
    const response = await axios.post(`${browserApiUrl}/api/job-logs/cleanup`, { days }, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  // Scheduled job methods
  async getScheduledJobs(params = {}) {
    const response = await axios.get(`${browserApiUrl}/api/scheduled-jobs`, {
      headers: this.getAuthHeader(),
      params
    });
    return response.data;
  },

  async getScheduledJob(id) {
    const response = await axios.get(`${browserApiUrl}/api/scheduled-jobs/${id}`, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  async createScheduledJob(jobData) {
    const response = await axios.post(`${browserApiUrl}/api/scheduled-jobs`, jobData, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  async updateScheduledJob(id, jobData) {
    const response = await axios.put(`${browserApiUrl}/api/scheduled-jobs/${id}`, jobData, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  async deleteScheduledJob(id) {
    const response = await axios.delete(`${browserApiUrl}/api/scheduled-jobs/${id}`, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  async runScheduledJob(id) {
    const response = await axios.post(`${browserApiUrl}/api/scheduled-jobs/${id}/run`, {}, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  async toggleScheduledJob(id, enabled) {
    const response = await axios.post(`${browserApiUrl}/api/scheduled-jobs/${id}/toggle`, { enabled }, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  // Gateway API methods
  async getGatewayStatus() {
    try {
      const response = await axios.get(`${browserApiUrl}/api/gateway/status`, {
        headers: this.getAuthHeader()
      });
      return response.data;
    } catch (error) {
      console.error('Error getting gateway status:', error);
      return { status: 'error', error: error.message };
    }
  },

  async getGatewayMetrics() {
    try {
      const response = await axios.get(`${browserApiUrl}/api/gateway/metrics`, {
        headers: this.getAuthHeader()
      });
      return response.data;
    } catch (error) {
      console.error('Error getting gateway metrics:', error);
      return { error: error.message };
    }
  },

  async resetGatewayMetrics() {
    try {
      const response = await axios.post(`${browserApiUrl}/api/gateway/reset-metrics`, {}, {
        headers: this.getAuthHeader()
      });
      return response.data;
    } catch (error) {
      console.error('Error resetting gateway metrics:', error);
      return { error: error.message };
    }
  },

  async getGatewayConfig() {
    try {
      const response = await axios.get(`${browserApiUrl}/api/gateway/config`, {
        headers: this.getAuthHeader()
      });
      return response.data;
    } catch (error) {
      console.error('Error getting gateway config:', error);
      return { error: error.message };
    }
  },

  // =========================================================
  // Credential API methods
  // =========================================================
  
  /**
   * Get all credentials
   * @param {Object} params - Query parameters
   * @param {number} [params.skip=0] - Number of records to skip
   * @param {number} [params.limit=100] - Maximum number of records to return
   * @param {boolean} [params.includeTags=true] - Whether to include tag information
   * @returns {Promise<Array>} List of credentials
   */
  getCredentials: async (params = {}) => {
    try {
      checkAuthHeader(); // Check auth header before request
      
      const queryParams = new URLSearchParams();
      if (params.skip !== undefined) queryParams.append('skip', params.skip);
      if (params.limit !== undefined) queryParams.append('limit', params.limit);
      if (params.includeTags !== undefined) queryParams.append('include_tags', params.includeTags);
      
      const url = `${browserApiUrl}/api/credentials/?${queryParams.toString()}`;
      console.log('Fetching credentials with URL:', url);
      console.log('Authorization header:', axios.defaults.headers.common['Authorization'] ? 'Present' : 'Missing');
      
      const response = await axios.get(url);
      console.log('Credentials API response:', response.status);
      return response.data;
    } catch (error) {
      console.error('Error fetching credentials:', error);
      console.error('Error details:', error.response ? error.response.data : 'No response data');
      throw error;
    }
  },
  
  /**
   * Get a credential by ID
   * @param {string} id - Credential ID
   * @param {boolean} [includeTags=true] - Whether to include tag information
   * @returns {Promise<Object>} Credential details
   */
  getCredential: async (id, includeTags = true) => {
    try {
      const response = await axios.get(`${browserApiUrl}/api/credentials/${id}?include_tags=${includeTags}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching credential ${id}:`, error);
      throw error;
    }
  },
  
  /**
   * Create a new credential
   * @param {Object} credential - Credential data
   * @returns {Promise<Object>} Created credential
   */
  createCredential: async (credential) => {
    try {
      const response = await axios.post(`${browserApiUrl}/api/credentials/`, credential);
      return response.data;
    } catch (error) {
      console.error('Error creating credential:', error);
      throw error;
    }
  },
  
  /**
   * Update a credential
   * @param {string} id - Credential ID
   * @param {Object} credential - Updated credential data
   * @returns {Promise<Object>} Updated credential
   */
  updateCredential: async (id, credential) => {
    try {
      const response = await axios.put(`${browserApiUrl}/api/credentials/${id}`, credential);
      return response.data;
    } catch (error) {
      console.error(`Error updating credential ${id}:`, error);
      throw error;
    }
  },
  
  /**
   * Delete a credential
   * @param {string} id - Credential ID
   * @returns {Promise<void>}
   */
  deleteCredential: async (id) => {
    try {
      await axios.delete(`${browserApiUrl}/api/credentials/${id}`);
    } catch (error) {
      console.error(`Error deleting credential ${id}:`, error);
      throw error;
    }
  },
  
  /**
   * Get credentials by tag ID
   * @param {string} tagId - Tag ID
   * @returns {Promise<Array>} List of credentials
   */
  getCredentialsByTag: async (tagId) => {
    try {
      const response = await axios.get(`${browserApiUrl}/api/credentials/tag/${tagId}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching credentials for tag ${tagId}:`, error);
      throw error;
    }
  },
  
  /**
   * Associate a credential with a tag
   * @param {Object} association - Association data
   * @param {string} association.credentialId - Credential ID
   * @param {string} association.tagId - Tag ID
   * @param {number} [association.priority=0] - Priority
   * @returns {Promise<Object>} Association details
   */
  associateCredentialWithTag: async (association) => {
    try {
      const response = await axios.post(`${browserApiUrl}/api/credentials/tag`, {
        credential_id: association.credentialId,
        tag_id: association.tagId,
        priority: association.priority || 0
      });
      return response.data;
    } catch (error) {
      console.error('Error associating credential with tag:', error);
      throw error;
    }
  },
  
  /**
   * Remove a credential from a tag
   * @param {string} credentialId - Credential ID
   * @param {string} tagId - Tag ID
   * @returns {Promise<void>}
   */
  removeCredentialFromTag: async (credentialId, tagId) => {
    try {
      await axios.delete(`${browserApiUrl}/api/credentials/tag/${credentialId}/${tagId}`);
    } catch (error) {
      console.error(`Error removing credential ${credentialId} from tag ${tagId}:`, error);
      throw error;
    }
  },
  
  /**
   * Test a credential against a device
   * @param {string} credentialId - Credential ID
   * @param {Object} [testData] - Test parameters
   * @param {string} [testData.deviceId] - Device ID
   * @param {string} [testData.hostname] - Device hostname
   * @param {string} [testData.deviceType] - Device type
   * @param {number} [testData.port=22] - Device port
   * @returns {Promise<Object>} Test result
   */
  testCredential: async (credentialId, testData = {}) => {
    try {
      const response = await axios.post(`${browserApiUrl}/api/credentials/test/${credentialId}`, {
        device_id: testData.deviceId,
        hostname: testData.hostname,
        device_type: testData.deviceType,
        port: testData.port || 22
      });
      return response.data;
    } catch (error) {
      console.error(`Error testing credential ${credentialId}:`, error);
      throw error;
    }
  },
  
  /**
   * Associate multiple credentials with multiple tags
   * @param {Object} bulkOperation - Bulk operation data
   * @param {Array<string>} bulkOperation.credentialIds - Credential IDs
   * @param {Array<string>} bulkOperation.tagIds - Tag IDs
   * @param {number} [priority=0] - Priority for the associations
   * @returns {Promise<Object>} Operation results
   */
  bulkAssociateCredentialsWithTags: async (bulkOperation, priority = 0) => {
    try {
      const response = await axios.post(`${browserApiUrl}/api/credentials/bulk/tag?priority=${priority}`, {
        credential_ids: bulkOperation.credentialIds,
        tag_ids: bulkOperation.tagIds
      });
      return response.data;
    } catch (error) {
      console.error('Error associating credentials with tags in bulk:', error);
      throw error;
    }
  },
  
  /**
   * Remove multiple credentials from multiple tags
   * @param {Object} bulkOperation - Bulk operation data
   * @param {Array<string>} bulkOperation.credentialIds - Credential IDs
   * @param {Array<string>} bulkOperation.tagIds - Tag IDs
   * @returns {Promise<Object>} Operation results
   */
  bulkRemoveCredentialsFromTags: async (bulkOperation) => {
    try {
      const response = await axios.delete(`${browserApiUrl}/api/credentials/bulk/tag`, {
        data: {
          credential_ids: bulkOperation.credentialIds,
          tag_ids: bulkOperation.tagIds
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error removing credentials from tags in bulk:', error);
      throw error;
    }
  },

  // Credential methods
  async getCredentials(params = {}) {
    const response = await axios.get(`${browserApiUrl}/api/credentials`, {
      headers: this.getAuthHeader(),
      params
    });
    return response.data;
  },

  async getCredential(id) {
    const response = await axios.get(`${browserApiUrl}/api/credentials/${id}`, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  async createCredential(credentialData) {
    const response = await axios.post(`${browserApiUrl}/api/credentials`, credentialData, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  async updateCredential(id, credentialData) {
    const response = await axios.put(`${browserApiUrl}/api/credentials/${id}`, credentialData, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  async deleteCredential(id) {
    const response = await axios.delete(`${browserApiUrl}/api/credentials/${id}`, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  async testCredential(id, testParams) {
    const response = await axios.post(`${browserApiUrl}/api/credentials/${id}/test`, testParams, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  // New credential tag association methods
  async addTagsToCredential(credentialId, tagIds) {
    const response = await axios.post(
      `${browserApiUrl}/api/credentials/${credentialId}/tags`,
      { tag_ids: tagIds },
      { headers: this.getAuthHeader() }
    );
    return response.data;
  },

  async removeTagsFromCredential(credentialId, tagIds) {
    const response = await axios.delete(
      `${browserApiUrl}/api/credentials/${credentialId}/tags`,
      { 
        headers: this.getAuthHeader(),
        data: { tag_ids: tagIds }
      }
    );
    return response.data;
  },

  async getTagsForCredential(credentialId) {
    const response = await axios.get(`${browserApiUrl}/api/credentials/${credentialId}/tags`, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },

  // Credential stats and dashboard
  async getCredentialStats() {
    const response = await axios.get(`${browserApiUrl}/api/credentials/stats`, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },
  
  async getTagCredentialStats(tagId) {
    const response = await axios.get(`${browserApiUrl}/api/credentials/stats/tag/${tagId}`, {
      headers: this.getAuthHeader()
    });
    return response.data;
  },
  
  async getSmartCredentialsForTag(tagId, limit = 5) {
    const response = await axios.post(`${browserApiUrl}/api/credentials/smart-select`, 
      { tag_id: tagId, limit: limit }, 
      { headers: this.getAuthHeader() }
    );
    return response.data;
  },
  
  async optimizeCredentialPriorities(tagId) {
    const response = await axios.post(`${browserApiUrl}/api/credentials/optimize-priorities/${tagId}`, 
      {}, 
      { headers: this.getAuthHeader() }
    );
    return response.data;
  },
  
  async reencryptCredentials(batchSize = 100) {
    const response = await axios.post(`${browserApiUrl}/api/credentials/reencrypt`, 
      {},
      { 
        headers: this.getAuthHeader(),
        params: { batch_size: batchSize }
      }
    );
    return response.data;
  },

  // Key management API methods
  async getKeys() {
    try {
      const response = await axios.get(`${browserApiUrl}/api/keys`, {
        headers: this.getAuthHeader()
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching keys:', error);
      throw error;
    }
  },

  async getKey(id) {
    try {
      const response = await axios.get(`${browserApiUrl}/api/keys/${id}`, {
        headers: this.getAuthHeader()
      });
      return response.data;
    } catch (error) {
      console.error(`Error fetching key ${id}:`, error);
      throw error;
    }
  },

  async createKey(keyData = {}) {
    try {
      const response = await axios.post(`${browserApiUrl}/api/keys`, keyData, {
        headers: {
          ...this.getAuthHeader(),
          'Content-Type': 'application/json'
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error creating key:', error);
      throw error;
    }
  },

  async activateKey(keyData) {
    try {
      const response = await axios.post(`${browserApiUrl}/api/keys/activate`, keyData, {
        headers: {
          ...this.getAuthHeader(),
          'Content-Type': 'application/json'
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error activating key:', error);
      throw error;
    }
  },

  async rotateKeys(rotateData = {}) {
    try {
      const response = await axios.post(`${browserApiUrl}/api/keys/rotate`, rotateData, {
        headers: {
          ...this.getAuthHeader(),
          'Content-Type': 'application/json'
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error rotating keys:', error);
      throw error;
    }
  },

  async createKeyBackup(backupData) {
    try {
      const response = await axios.post(`${browserApiUrl}/api/keys/backup`, backupData, {
        headers: {
          ...this.getAuthHeader(),
          'Content-Type': 'application/json'
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error creating key backup:', error);
      throw error;
    }
  },

  async restoreKeys(restoreData) {
    try {
      const response = await axios.post(`${browserApiUrl}/api/keys/restore`, restoreData, {
        headers: {
          ...this.getAuthHeader(),
          'Content-Type': 'application/json'
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error restoring keys:', error);
      throw error;
    }
  },

  // Admin Settings methods
  async getAdminSettings() {
    const response = await axios.get(`${browserApiUrl}/api/admin-settings`, {
      headers: this.getAuthHeader()
    });
    return response;
  },

  async getAdminSettingsByCategory() {
    const response = await axios.get(`${browserApiUrl}/api/admin-settings/categories`, {
      headers: this.getAuthHeader()
    });
    return response;
  },

  async getAdminSetting(id) {
    const response = await axios.get(`${browserApiUrl}/api/admin-settings/${id}`, {
      headers: this.getAuthHeader()
    });
    return response;
  },

  async getAdminSettingByKey(key) {
    const response = await axios.get(`${browserApiUrl}/api/admin-settings/key/${key}`, {
      headers: this.getAuthHeader()
    });
    return response;
  },

  async createAdminSetting(settingData) {
    const response = await axios.post(`${browserApiUrl}/api/admin-settings`, settingData, {
      headers: this.getAuthHeader()
    });
    return response;
  },

  async updateAdminSetting(id, settingData) {
    const response = await axios.put(`${browserApiUrl}/api/admin-settings/${id}`, settingData, {
      headers: this.getAuthHeader()
    });
    return response;
  },

  async updateAdminSettingValue(key, valueData) {
    const response = await axios.put(`${browserApiUrl}/api/admin-settings/key/${key}/value`, valueData, {
      headers: this.getAuthHeader()
    });
    return response;
  },

  async deleteAdminSetting(id) {
    const response = await axios.delete(`${browserApiUrl}/api/admin-settings/${id}`, {
      headers: this.getAuthHeader()
    });
    return response;
  },

  async initializeAdminSettings() {
    const response = await axios.post(`${browserApiUrl}/api/admin-settings/initialize`, {}, {
      headers: this.getAuthHeader()
    });
    return response;
  },

  async applyAdminSetting(id) {
    const response = await axios.post(`${browserApiUrl}/api/admin-settings/apply/${id}`, {}, {
      headers: this.getAuthHeader()
    });
    return response;
  },

  async applyAllAdminSettings() {
    const response = await axios.post(`${browserApiUrl}/api/admin-settings/apply-all`, {}, {
      headers: this.getAuthHeader()
    });
    return response;
  },
}

// Export services
export default apiClient;

// Individual service exports with domain-specific methods
export const deviceService = {
  getDevices: apiClient.getDevices.bind(apiClient),
  getDevice: apiClient.getDevice.bind(apiClient),
  createDevice: apiClient.createDevice.bind(apiClient),
  updateDevice: apiClient.updateDevice.bind(apiClient),
  deleteDevice: apiClient.deleteDevice.bind(apiClient),
  backupDevice: apiClient.backupDevice.bind(apiClient),
  checkReachability: apiClient.checkDeviceReachability.bind(apiClient)
};

export const tagService = {
  getTags: apiClient.getTags.bind(apiClient),
  getTag: apiClient.getTag.bind(apiClient),
  createTag: apiClient.createTag.bind(apiClient),
  updateTag: apiClient.updateTag.bind(apiClient),
  deleteTag: apiClient.deleteTag.bind(apiClient),
  getDevicesForTag: apiClient.getDevicesForTag.bind(apiClient),
  getTagsForDevice: apiClient.getTagsForDevice.bind(apiClient),
  assignTagsToDevices: apiClient.assignTagsToDevices.bind(apiClient),
  removeTagsFromDevices: apiClient.removeTagsFromDevices.bind(apiClient)
};

// Add the missing tagRuleService
export const tagRuleService = {
  getTagRules: apiClient.getTagRules.bind(apiClient),
  getTagRule: apiClient.getTagRule.bind(apiClient),
  createTagRule: apiClient.createTagRule.bind(apiClient),
  updateTagRule: apiClient.updateTagRule.bind(apiClient),
  deleteTagRule: apiClient.deleteTagRule.bind(apiClient),
  applyTagRule: apiClient.applyTagRule.bind(apiClient),
  testRule: apiClient.testRule.bind(apiClient)
};

export const backupService = {
  getBackups: apiClient.getBackups.bind(apiClient),
  getBackup: apiClient.getBackup.bind(apiClient),
  getBackupContent: apiClient.getBackupContent.bind(apiClient),
  compareBackups: apiClient.compareBackups.bind(apiClient),
  restoreBackup: apiClient.restoreBackup.bind(apiClient),
  deleteBackup: apiClient.deleteBackup.bind(apiClient)
};

export const jobLogsService = {
  getJobLogs: apiClient.getJobLogs.bind(apiClient),
  getJobLog: apiClient.getJobLog.bind(apiClient),
  getJobLogEntries: apiClient.getJobLogEntries.bind(apiClient),
  deleteJobLog: apiClient.deleteJobLog.bind(apiClient),
  updateRetentionPolicy: apiClient.updateRetentionPolicy.bind(apiClient),
  cleanupJobLogs: apiClient.cleanupJobLogs.bind(apiClient)
};

export const scheduledJobsService = {
  getScheduledJobs: apiClient.getScheduledJobs.bind(apiClient),
  getScheduledJob: apiClient.getScheduledJob.bind(apiClient),
  createScheduledJob: apiClient.createScheduledJob.bind(apiClient),
  updateScheduledJob: apiClient.updateScheduledJob.bind(apiClient),
  deleteScheduledJob: apiClient.deleteScheduledJob.bind(apiClient),
  runScheduledJob: apiClient.runScheduledJob.bind(apiClient),
  toggleScheduledJob: apiClient.toggleScheduledJob.bind(apiClient)
};

// Admin Settings API
export const adminSettingsApi = {
  // Get all admin settings
  getSettings: (params = {}) => {
    return axios.get(`${browserApiUrl}/api/admin-settings/`, { params });
  },
  
  // Get settings grouped by category
  getSettingsByCategory: () => {
    return axios.get(`${browserApiUrl}/api/admin-settings/by-category`);
  },
  
  // Get a specific setting by ID
  getSetting: (id) => {
    return axios.get(`${browserApiUrl}/api/admin-settings/${id}`);
  },
  
  // Get a specific setting by key
  getSettingByKey: (key) => {
    return axios.get(`${browserApiUrl}/api/admin-settings/key/${key}`);
  },
  
  // Create a new setting
  createSetting: (data) => {
    return axios.post(`${browserApiUrl}/api/admin-settings/`, data);
  },
  
  // Update a setting
  updateSetting: (id, data) => {
    return axios.put(`${browserApiUrl}/api/admin-settings/${id}`, data);
  },
  
  // Update a setting value by key
  updateSettingValue: (key, data) => {
    return axios.patch(`${browserApiUrl}/api/admin-settings/key/${key}`, data);
  },
  
  // Delete a setting
  deleteSetting: (id) => {
    return axios.delete(`${browserApiUrl}/api/admin-settings/${id}`);
  },
  
  // Initialize default settings
  initializeDefaultSettings: () => {
    return axios.post(`${browserApiUrl}/api/admin-settings/initialize`);
  }
}; 