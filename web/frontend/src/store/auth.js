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
    currentUser: (state) => state.user
  },
  
  actions: {
    async login(username, password) {
      this.loading = true
      this.error = null
      
      try {
        const response = await authService.login(username, password)
        this.token = response.access_token
        await this.fetchCurrentUser()
        return true
      } catch (error) {
        this.error = error.response?.data?.detail || 'Login failed'
        console.error('Login error:', error)
        return false
      } finally {
        this.loading = false
      }
    },
    
    async fetchCurrentUser() {
      if (!this.token) return null
      
      this.loading = true
      
      try {
        const user = await authService.getCurrentUser()
        this.user = user
        return user
      } catch (error) {
        console.error('Failed to fetch user:', error)
        // If we can't get the user, the token might be invalid
        if (error.response?.status === 401) {
          this.logout()
        }
        return null
      } finally {
        this.loading = false
      }
    },
    
    logout() {
      authService.logout()
      this.token = null
      this.user = null
    }
  }
}) 