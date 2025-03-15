import { defineStore } from 'pinia'
import { authService } from '../api/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('access_token') || null,
    loading: false,
    error: null
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.token,
    hasUserData: (state) => !!state.user,
    username: (state) => state.user?.username || 'User'
  },
  
  actions: {
    async login(username, password) {
      this.loading = true
      this.error = null
      
      try {
        const data = await authService.login(username, password)
        this.token = data.access_token
        
        // After successful login, fetch the user data
        try {
          await this.fetchCurrentUser()
        } catch (userError) {
          console.error('Failed to fetch user after login:', userError)
          // Continue with login even if user fetch fails
          // The user can retry fetching later
        }
        
        return true
      } catch (error) {
        console.error('Login failed:', error)
        this.error = error.message || 'Login failed'
        return false
      } finally {
        this.loading = false
      }
    },
    
    async fetchCurrentUser() {
      this.loading = true
      this.error = null
      
      try {
        // Only attempt to fetch if we have a token
        if (!this.token) {
          console.warn('Cannot fetch user: No token available')
          this.error = 'Authentication required'
          throw new Error('Authentication required')
        }
        
        const userData = await authService.getCurrentUser()
        this.user = userData
        return userData
      } catch (error) {
        console.error('Failed to fetch current user:', error)
        
        // Handle token invalidation
        if (error.isAuthError || error.response?.status === 401) {
          console.log('Token invalid, clearing user data and token')
          this.user = null
          this.token = null
          localStorage.removeItem('access_token')
          this.error = 'Session expired. Please log in again.'
        } else if (error.response?.status === 404) {
          // If the endpoint doesn't exist, don't treat it as an error
          // Just set a minimal user object
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
      authService.logout()
      this.user = null
      this.token = null
      this.error = null
    },
    
    clearError() {
      this.error = null
    }
  }
}) 