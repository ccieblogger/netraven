import { defineStore } from 'pinia'
import apiClient from '../api/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('access_token') || null,
    tokenScopes: [],
    loading: false,
    error: null
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.token,
    hasUserData: (state) => !!state.user,
    username: (state) => state.user?.username || 'User',
    isTokenValid: (state) => {
      if (!state.token) return false
      
      try {
        if (typeof state.token !== 'string' || state.token.split('.').length !== 3) {
          console.warn('Token has invalid format')
          return false
        }
        
        const payload = JSON.parse(atob(state.token.split('.')[1]))
        
        if (!payload.exp) {
          console.warn('Token has no expiration')
          return true
        }
        
        const now = Math.floor(Date.now() / 1000)
        return now < payload.exp
      } catch (e) {
        console.error('Error validating token:', e)
        return false
      }
    },
    
    hasPermission: (state) => (permission) => {
      if (!state.token) return false
      
      try {
        const payload = JSON.parse(atob(state.token.split('.')[1]))
        
        if (!payload.scope) {
          console.warn('Token has no scope property')
          return false
        }
        
        return payload.scope.includes(permission) || payload.scope.includes('admin:*')
      } catch (e) {
        console.error('Error checking token permission:', e)
        return false
      }
    },
    
    canManageDevices: (state) => {
      return state.hasPermission('write:devices')
    }
  },
  
  actions: {
    async login(username, password) {
      this.loading = true
      this.error = null
      
      try {
        const result = await apiClient.login(username, password)
        
        if (result.success) {
          this.token = result.data.access_token
          
          try {
            const payload = JSON.parse(atob(this.token.split('.')[1]))
            this.tokenScopes = payload.scope || []
            console.log('Extracted token scopes:', this.tokenScopes)
          } catch (e) {
            console.error('Error extracting token scopes:', e)
            this.tokenScopes = []
          }
          
          try {
            await this.fetchCurrentUser()
          } catch (userError) {
            console.error('Failed to fetch user after login:', userError)
          }
          
          return true
        } else {
          this.error = result.message || 'Login failed'
          return false
        }
      } catch (error) {
        console.error('Login failed:', error)
        this.error = error.message || 'Login failed'
        return false
      } finally {
        this.loading = false
      }
    },
    
    validateToken() {
      if (!this.token) return false
      
      const isValid = this.isTokenValid
      
      if (!isValid) {
        console.warn('Token validation failed, clearing token')
        this.clearAuth()
        return false
      }
      
      try {
        const payload = JSON.parse(atob(this.token.split('.')[1]))
        this.tokenScopes = payload.scope || []
      } catch (e) {
        console.error('Error extracting token scopes during validation:', e)
        this.tokenScopes = []
      }
      
      return true
    },
    
    checkPermission(permission) {
      if (!this.validateToken()) return false
      
      return this.hasPermission(permission)
    },
    
    verifyDeviceManagementPermission() {
      const hasPermission = this.checkPermission('write:devices')
      
      if (!hasPermission) {
        console.error('User lacks device management permissions')
        this.error = 'You do not have permission to manage devices'
      }
      
      return hasPermission
    },
    
    clearAuth() {
      this.user = null
      this.token = null
      this.tokenScopes = []
      localStorage.removeItem('access_token')
    },
    
    async fetchCurrentUser() {
      this.loading = true
      this.error = null
      
      try {
        if (!this.validateToken()) {
          this.error = 'Authentication required'
          throw new Error('Authentication required')
        }
        
        const userData = await apiClient.getCurrentUser()
        this.user = userData
        return userData
      } catch (error) {
        console.error('Failed to fetch current user:', error)
        
        if (error.isAuthError || error.response?.status === 401) {
          console.log('Token invalid, clearing user data and token')
          this.clearAuth()
          this.error = 'Session expired. Please log in again.'
        } else if (error.response?.status === 404) {
          console.log('User endpoint not found (404), using minimal user data')
          this.user = { username: 'User' }
          this.error = null
          return this.user
        } else {
          this.error = 'Failed to load user data'
        }
        
        throw error
      } finally {
        this.loading = false
      }
    },
    
    logout() {
      apiClient.logout()
      this.clearAuth()
      this.error = null
    },
    
    clearError() {
      this.error = null
    }
  }
}) 