import { defineStore } from 'pinia';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: null, // Stores the JWT token
    user: null,  // Stores decoded user information (e.g., username, id)
    role: null,  // Stores user role for access control
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
    userRole: (state) => state.role,
  },
  actions: {
    // Action to set auth state after successful login
    setAuth(token, user) {
      this.token = token;
      this.user = user;
      this.role = user?.role || null; // Assuming user object has a role property
      // Optionally persist token (e.g., localStorage) here
      // localStorage.setItem('authToken', token);
    },
    // Action to clear auth state on logout
    logout() {
      this.token = null;
      this.user = null;
      this.role = null;
      // Optionally remove persisted token
      // localStorage.removeItem('authToken');
      // Optionally redirect to login page
      // router.push({ name: 'Login' }); 
    },
    // Action to potentially load token from storage on app load
    loadToken() {
      // const token = localStorage.getItem('authToken');
      // if (token) {
      //   // Need a way to validate the token and get user info if loading from storage
      //   // This might involve an API call to /users/me or decoding the token (if not expired)
      //   // For now, just setting the token as an example
      //   // this.token = token; 
      //   // Decode token to get user info (basic example, needs validation)
      //   try {
      //      const payload = JSON.parse(atob(token.split('.')[1]));
      //      if (payload.exp * 1000 > Date.now()) { // Check expiry
      //          this.token = token;
      //          this.user = { username: payload.sub }; // Example user info
      //          this.role = payload.role; // Assuming role is in token
      //      } else {
      //          this.logout(); // Token expired
      //      }
      //   } catch (e) {
      //      console.error('Failed to decode token', e);
      //      this.logout();
      //   }
      // }
    }
  }
});
