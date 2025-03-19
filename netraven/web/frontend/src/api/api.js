import axios from 'axios'

// Configure axios defaults
axios.defaults.withCredentials = false;

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

// If VUE_APP_API_URL is not set, use hostname for dynamic resolution
if (!process.env.VUE_APP_API_URL) {
  const hostname = window.location.hostname;
  browserApiUrl = `http://${hostname}:8000`;
  console.log('Using production API URL with hostname:', hostname);
}

console.log('Final API URL:', browserApiUrl);

// Setup Axios interceptors for authentication handling
axios.interceptors.response.use(
  response => {
    // Pass through successful responses
    return response;
  },
  error => {
    // Handle authentication errors
    if (error.response && error.response.status === 401) {
      console.warn('Authentication error intercepted:', error.response.data);
      
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
        
        if (now >= payload.exp) {
          console.warn('Token has expired, clearing from localStorage');
          localStorage.removeItem('access_token');
          return {};
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

  // Authentication methods
  async login(username, password) {
    try {
      // Send JSON data instead of form data for Pydantic 2.x compatibility
      const response = await axios.post(`${browserApiUrl}/api/auth/token`, {
        username: username,
        password: password
      }, {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        withCredentials: false
      });
      
      // Store token in localStorage
      localStorage.setItem('access_token', response.data.access_token);
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Login error:', error);
      
      // Handle different error scenarios
      if (error.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        return {
          success: false,
          status: error.response.status,
          message: error.response.data.detail || 'Authentication failed'
        };
      } else if (error.request) {
        // The request was made but no response was received
        return {
          success: false,
          message: 'No response from server. Please check your connection.'
        };
      } else {
        // Something happened in setting up the request that triggered an Error
        return {
          success: false,
          message: 'Error setting up request: ' + error.message
        };
      }
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
    localStorage.removeItem('access_token');
    return true;
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
  }
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