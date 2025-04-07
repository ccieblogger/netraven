<template>
  <div class="p-4 flex flex-col items-center justify-center min-h-screen">
    <h1 class="text-2xl font-semibold">Login</h1>
    <p class="mt-2">Please log in to continue. (Placeholder)</p>
    <!-- Add login form here -->
    <form @submit.prevent="handleLogin" class="mt-4 space-y-4 w-full max-w-xs">
      <div>
        <label for="username" class="block text-sm font-medium text-gray-700">Username</label>
        <input type="text" id="username" v.model="username" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm">
      </div>
      <div>
        <label for="password" class="block text-sm font-medium text-gray-700">Password</label>
        <input type="password" id="password" v.model="password" required class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm">
      </div>
      <button type="submit" class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
        Log In
      </button>
      <p v-if="errorMsg" class="text-sm text-red-600">{{ errorMsg }}</p>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue';
// import { useRouter } from 'vue-router';
// import { useAuthStore } from '../store/auth';
// import api from '../services/api';

const username = ref('');
const password = ref('');
const errorMsg = ref(null);
// const router = useRouter();
// const authStore = useAuthStore();

const handleLogin = async () => {
  errorMsg.value = null;
  console.log('Login attempt (placeholder)', username.value);
  // Placeholder: Implement actual login logic using authStore and API client
  // try {
  //   // Use OAuth2PasswordRequestForm format expected by backend
  //   const formData = new URLSearchParams();
  //   formData.append('username', username.value);
  //   formData.append('password', password.value);
  // 
  //   const response = await api.post('/auth/token', formData, {
  //      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  //   });
  // 
  //   const token = response.data.access_token;
  //   // Fetch user details (or decode token if it contains user info)
  //   // const userResponse = await api.get('/users/me'); // Assuming a /users/me endpoint
  //   // const user = userResponse.data;
  //   const user = { username: username.value, role: 'user' }; // Placeholder user
  // 
  //   authStore.setAuth(token, user);
  //   router.push({ name: 'Dashboard' }); // Redirect to dashboard on success
  // } catch (error) {
  //   console.error('Login failed:', error.response?.data?.detail || error.message);
  //   errorMsg.value = error.response?.data?.detail || 'Login failed. Please check credentials.';
  //   authStore.logout(); // Ensure any partial auth state is cleared
  // }
};
</script>
