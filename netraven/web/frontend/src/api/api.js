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

// Determine the API URL
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

// Determine the API URL to use
if (envApiBaseUrl) {
  // Use environment variable if available
  browserApiUrl = envApiBaseUrl;
  console.log('Using configured API URL from environment');
} else if (isWsl || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
  // Local or WSL environment - use localhost with port 8000
  browserApiUrl = 'http://localhost:8000';
  console.log('Using localhost API URL');
} else {
  // Production/Docker environment
  // If we're accessing the frontend from outside Docker via 8080 port
  // we need to construct the API URL using the same hostname but port 8000
  const hostname = window.location.hostname;
  browserApiUrl = `http://${hostname}:8000`;
  console.log('Using production API URL with hostname:', hostname);
}

console.log('Final API URL:', browserApiUrl);

// Create API client
const apiClient = {
  // Get auth header for authenticated requests
  getAuthHeader() {
    const token = localStorage.getItem('access_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  },

  // Authentication methods
  async login(username, password) {
    try {
      // Create form data
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await axios.post(`${browserApiUrl}/api/auth/token`, formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
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

  async createDevice(deviceData) {
    const response = await axios.post(`${browserApiUrl}/api/devices`, deviceData, {
      headers: this.getAuthHeader()
    });
    return response.data;
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

// Create individual service objects that use the main apiClient
export const deviceService = {
  getDevices: () => apiClient.getDevices(),
  getDevice: (id) => apiClient.getDevice(id),
  createDevice: (deviceData) => apiClient.createDevice(deviceData),
  updateDevice: (id, deviceData) => apiClient.updateDevice(id, deviceData),
  deleteDevice: (id) => apiClient.deleteDevice(id),
  backupDevice: (id) => apiClient.backupDevice(id),
  checkDeviceReachability: (id) => apiClient.checkDeviceReachability(id)
}

export const backupService = {
  getBackups: (params) => apiClient.getBackups(params),
  getBackup: (id) => apiClient.getBackup(id),
  getBackupContent: (id) => apiClient.getBackupContent(id),
  compareBackups: (backup1Id, backup2Id) => apiClient.compareBackups(backup1Id, backup2Id),
  restoreBackup: (id) => apiClient.restoreBackup(id),
  deleteBackup: (id) => apiClient.deleteBackup(id)
}

export const jobLogsService = {
  getJobLogs: (params) => apiClient.getJobLogs(params),
  getJobLog: (id, includeEntries) => apiClient.getJobLog(id, includeEntries),
  getJobLogEntries: (id, params) => apiClient.getJobLogEntries(id, params),
  deleteJobLog: (id) => apiClient.deleteJobLog(id)
}

export const scheduledJobsService = {
  getScheduledJobs: (params) => apiClient.getScheduledJobs(params),
  getScheduledJob: (id) => apiClient.getScheduledJob(id),
  createScheduledJob: (jobData) => apiClient.createScheduledJob(jobData),
  updateScheduledJob: (id, jobData) => apiClient.updateScheduledJob(id, jobData),
  deleteScheduledJob: (id) => apiClient.deleteScheduledJob(id),
  runScheduledJob: (id) => apiClient.runScheduledJob(id),
  toggleScheduledJob: (id, enabled) => apiClient.toggleScheduledJob(id, enabled)
}

export default apiClient 