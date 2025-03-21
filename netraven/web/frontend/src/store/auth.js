import { defineStore } from 'pinia'
import apiClient from '../api/api'

// Constants for token handling
const TOKEN_REFRESH_BUFFER = 5 * 60; // 5 minutes in seconds before expiration to trigger refresh
const TOKEN_CHECK_INTERVAL = 30 * 1000; // Check token validity every 30 seconds

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('access_token') || null,
    tokenScopes: [],
    loading: false,
    error: null,
    refreshInterval: null,
    tokenExpiration: null
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.token,
    hasUserData: (state) => !!state.user,
    username: (state) => state.user?.username || 'User',
    
    // Check if token is valid and not expired
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
    
    // Calculate seconds until token expiration
    secondsUntilExpiration: (state) => {
      if (!state.token) return 0
      
      try {
        const payload = JSON.parse(atob(state.token.split('.')[1]))
        
        if (!payload.exp) return Infinity
        
        const now = Math.floor(Date.now() / 1000)
        return Math.max(0, payload.exp - now)
      } catch (e) {
        console.error('Error calculating token expiration:', e)
        return 0
      }
    },
    
    // Check if the token needs to be refreshed soon
    shouldRefreshToken: (state) => {
      return state.isTokenValid && state.secondsUntilExpiration < TOKEN_REFRESH_BUFFER
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
    
    hasRole: (state) => (role) => {
      if (!state.token) return false
      
      try {
        // First check if user has admin role via scope
        const payload = JSON.parse(atob(state.token.split('.')[1]))
        
        // Admin role check
        if (role === 'admin' && payload.scope && 
            (payload.scope.includes('admin:*') || payload.scope.includes('admin'))) {
          return true
        }
        
        // Check if roles are directly in the token
        if (payload.roles && Array.isArray(payload.roles)) {
          return payload.roles.includes(role)
        }
        
        // Check if roles are in the user object
        if (state.user && state.user.roles && Array.isArray(state.user.roles)) {
          return state.user.roles.includes(role)
        }
        
        // Special case for admin role - check for admin scopes
        if (role === 'admin' && payload.scope) {
          // If any scope starts with 'admin:', user has admin role
          if (typeof payload.scope === 'string') {
            return payload.scope.split(' ').some(s => s.startsWith('admin:'))
          } else if (Array.isArray(payload.scope)) {
            return payload.scope.some(s => s.startsWith('admin:'))
          }
        }
        
        return false
      } catch (e) {
        console.error('Error checking user role:', e)
        return false
      }
    },
    
    canManageDevices: (state) => {
      return state.hasPermission('write:devices')
    }
  },
  
  actions: {
    // Setup token refresh mechanism
    setupTokenRefresh() {
      // Clear any existing interval
      if (this.refreshInterval) {
        clearInterval(this.refreshInterval)
      }
      
      // Only setup refresh interval if we have a token
      if (this.token) {
        console.log('Setting up token refresh mechanism')
        
        // Check token validity and expiration immediately
        this.checkTokenExpiration()
        
        // Set up interval to check token expiration
        this.refreshInterval = setInterval(() => {
          this.checkTokenExpiration()
        }, TOKEN_CHECK_INTERVAL)
      }
    },
    
    // Check if token needs refreshing and refresh if needed
    async checkTokenExpiration() {
      // Skip if loading or no token
      if (this.loading || !this.token) return
      
      if (this.isTokenValid) {
        try {
          const secondsLeft = this.secondsUntilExpiration
          
          // If token is close to expiration, refresh it
          if (secondsLeft < TOKEN_REFRESH_BUFFER) {
            console.log(`Token expiring soon (${secondsLeft}s left), refreshing...`)
            await this.refreshToken()
          } else {
            // Log remaining time for debugging (only log occasionally to avoid spam)
            if (secondsLeft % 300 < 30) { // Log roughly every 5 minutes
              console.log(`Token still valid for ${Math.floor(secondsLeft / 60)} minutes ${secondsLeft % 60} seconds`)
            }
          }
        } catch (e) {
          console.error('Error checking token expiration:', e)
        }
      } else if (this.token) {
        console.warn('Token is invalid or expired, clearing token')
        this.clearAuth()
      }
    },
    
    // Refresh the current token
    async refreshToken() {
      this.loading = true
      this.error = null
      
      try {
        // Call API client refresh token method
        const newToken = await apiClient.refreshToken()
        
        if (newToken) {
          // Update store with new token
          this.token = newToken
          
          // Extract token scopes and expiration
          try {
            const payload = JSON.parse(atob(newToken.split('.')[1]))
            this.tokenScopes = payload.scope || []
            
            if (payload.exp) {
              this.tokenExpiration = new Date(payload.exp * 1000)
              console.log(`Token refreshed, new expiration: ${this.tokenExpiration.toISOString()}`)
            }
          } catch (e) {
            console.error('Error extracting token data after refresh:', e)
          }
          
          return true
        } else {
          console.warn('Token refresh returned no token')
          return false
        }
      } catch (e) {
        console.error('Token refresh failed:', e)
        this.error = 'Failed to refresh authentication'
        
        // If the error is critical (invalid token), clear auth
        if (e.isAuthError) {
          this.clearAuth()
        }
        
        return false
      } finally {
        this.loading = false
      }
    },
    
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
            
            // Store token expiration
            if (payload.exp) {
              this.tokenExpiration = new Date(payload.exp * 1000)
            }
            
            console.log('Extracted token scopes:', this.tokenScopes)
          } catch (e) {
            console.error('Error extracting token scopes:', e)
            this.tokenScopes = []
          }
          
          // Setup token refresh mechanism
          this.setupTokenRefresh()
          
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
        
        // Update token expiration
        if (payload.exp) {
          this.tokenExpiration = new Date(payload.exp * 1000)
        }
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
      this.tokenExpiration = null
      localStorage.removeItem('access_token')
      
      // Clear token refresh interval
      if (this.refreshInterval) {
        clearInterval(this.refreshInterval)
        this.refreshInterval = null
      }
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