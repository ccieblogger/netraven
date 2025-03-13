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
      console.log('Auth Store: Login attempt started for', username);
      this.loading = true;
      this.error = null;
      
      try {
        console.log('Auth Store: Calling authService.login');
        const response = await authService.login(username, password);
        console.log('Auth Store: Login successful, token received', response);
        
        // Make sure we have a token
        if (!response || !response.access_token) {
          console.error('Auth Store: No token received in response', response);
          throw new Error('Invalid server response - no token received');
        }
        
        // Store the token in the store state
        this.token = response.access_token;
        
        // Make sure it's also in localStorage for persistence
        localStorage.setItem('access_token', response.access_token);
        console.log('Auth Store: Token stored in localStorage', {
          storeToken: this.token?.substring(0, 10) + '...',
          localStorageToken: localStorage.getItem('access_token')?.substring(0, 10) + '...'
        });
        
        // Try to fetch the current user
        try {
          console.log('Auth Store: Attempting to fetch user details');
          await this.fetchCurrentUser();
          console.log('Auth Store: User details fetched successfully');
        } catch (userError) {
          console.warn('Auth Store: Could not fetch user details, but login was successful', userError);
          // Don't fail the login if we can't fetch the user details
        }
        
        return true;
      } catch (error) {
        console.error('Auth Store: Login failed', error);
        
        // Handle different types of errors (network, server, etc.)
        if (error.message?.includes('NetworkError') || error.message?.includes('Failed to fetch')) {
          this.error = 'Network error. Please check your connection.';
        } else if (error.response?.status === 401 || error.message?.includes('401')) {
          this.error = 'Invalid username or password.';
        } else if (error.response?.data?.detail) {
          this.error = error.response.data.detail;
        } else {
          this.error = error.message || 'Login failed. Please try again.';
        }
        
        return false;
      } finally {
        this.loading = false;
      }
    },
    
    async fetchCurrentUser() {
      if (!this.token) {
        console.warn('Auth Store: Cannot fetch user without token');
        return null;
      }
      
      console.log('Auth Store: Token exists, attempting to fetch user');
      this.loading = true;
      
      try {
        console.log('Auth Store: Fetching current user');
        const user = await authService.getCurrentUser();
        console.log('Auth Store: User data received', user);
        this.user = user;
        return user;
      } catch (error) {
        console.error('Auth Store: Failed to fetch user', error);
        // If we can't get the user, the token might be invalid
        if (error.response?.status === 401) {
          console.log('Auth Store: Token invalid, logging out');
          this.logout();
        }
        throw error;
      } finally {
        this.loading = false;
      }
    },
    
    logout() {
      console.log('Auth Store: Logging out');
      authService.logout();
      this.token = null;
      this.user = null;
      
      // Force redirect to login page
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
  }
}) 