import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import api from '../services/api';
import router from '../router'; // Import router for redirection

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('authToken') || null); // Load token from localStorage on init
  const user = ref(JSON.parse(localStorage.getItem('authUser') || 'null')); // Load user info
  const loginError = ref(null);
  const isLoading = ref(false);
  const username = ref(''); // Added reactive username
  const password = ref(''); // Added reactive password

  // Computed properties for easy access
  const isAuthenticated = computed(() => !!token.value);
  const userRole = computed(() => user.value?.role || null);

  // Function to set auth data in state and localStorage
  function setAuthData(newToken, userData) {
    user.value = userData;
    token.value = newToken;
    localStorage.setItem('authToken', newToken);
    localStorage.setItem('authUser', JSON.stringify(userData));
    // Set Axios header immediately
    api.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
  }

  // Function to clear auth data
  function clearAuthData() {
    user.value = null;
    token.value = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('authUser');
    // Remove Axios header
    delete api.defaults.headers.common['Authorization'];
  }

  // Attempt to load user profile if token exists but user data doesn't (e.g., after refresh)
  // This assumes an endpoint like /users/me exists
  async function fetchUserProfile() {
    if (token.value && !user.value) {
      isLoading.value = true;
      try {
        // Set header first in case it wasn't set on initial load
        api.defaults.headers.common['Authorization'] = `Bearer ${token.value}`;
        const response = await api.get('/users/me');
        setAuthData(token.value, response.data); // Update user data
      } catch (err) {
        console.error("Failed to fetch user profile on load:", err);
        // Token might be invalid/expired, clear it
        clearAuthData();
      } finally {
        isLoading.value = false;
      }
    }
  }

  // Login action
  async function login(credentials) {
    loginError.value = null;

    try {
      // Use URLSearchParams to format the payload as x-www-form-urlencoded
      const payload = new URLSearchParams();
      payload.append('username', credentials.username);
      payload.append('password', credentials.password);

      const response = await api.post('/auth/token', payload, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      const newToken = response.data.access_token;
      // After getting token, fetch user details
      api.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
      const userResponse = await api.get('/users/me'); 
      
      setAuthData(newToken, userResponse.data);
      
      // Redirect to dashboard or intended route
      const redirectPath = router.currentRoute.value.query.redirect || '/dashboard';
      router.push(redirectPath); 

    } catch (err) {
      loginError.value = err.response?.data?.detail || 'Login failed. Please check credentials.';
      console.error("Login Error:", err);
      clearAuthData(); // Clear any potentially partially set data
      throw err; // Re-throw error for handling in Login.vue
    } finally {
      isLoading.value = false;
    }
  }

  // Logout action
  function logout() {
    clearAuthData();
    router.push('/login'); // Redirect to login page
  }

  return { 
    token, user, loginError, isLoading, isAuthenticated, userRole, username, password,
    login, logout, fetchUserProfile, clearAuthData 
  };
});
