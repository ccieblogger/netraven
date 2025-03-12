import axios from 'axios'

// Create base axios instance
const api = axios.create({
  baseURL: process.env.VUE_APP_API_URL || 'http://localhost:8082',
  headers: {
    'Content-Type': 'application/json'
  }
})

// Add request interceptor to attach the authentication token
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// Add response interceptor to handle token expiration
api.interceptors.response.use(
  response => {
    return response
  },
  error => {
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
    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)
    
    const response = await api.post('/api/auth/token', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })
    localStorage.setItem('access_token', response.data.access_token)
    return response.data
  },
  
  async getCurrentUser() {
    const response = await api.get('/api/auth/users/me')
    return response.data
  },
  
  logout() {
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
    const response = await api.post('/api/devices', deviceData)
    return response.data
  },
  
  async updateDevice(id, deviceData) {
    const response = await api.put(`/api/devices/${id}`, deviceData)
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