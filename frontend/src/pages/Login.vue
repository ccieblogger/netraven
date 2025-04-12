<template>
  <div class="bg-content min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8">
    <div class="sm:mx-auto sm:w-full sm:max-w-md">
      <div class="flex justify-center">
        <h1 class="text-3xl font-bold">
          <span class="text-primary">Net</span><span class="text-text-primary">Raven</span>
        </h1>
      </div>
      <h2 class="mt-6 text-center text-3xl font-extrabold text-text-primary">
        Sign in to your account
      </h2>
    </div>

    <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
      <NrCard className="px-4 py-8 shadow sm:rounded-lg sm:px-10">
        <form @submit.prevent="handleLogin" class="space-y-6">
          <div>
            <label for="username" class="block text-sm font-medium text-text-primary">
              Username
            </label>
            <div class="mt-1">
              <input
                id="username"
                name="username"
                type="text"
                autocomplete="username"
                required
                v-model="username"
                class="appearance-none block w-full px-3 py-2 border border-divider rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
              />
            </div>
          </div>

          <div>
            <label for="password" class="block text-sm font-medium text-text-primary">
              Password
            </label>
            <div class="mt-1">
              <input
                id="password"
                name="password"
                type="password"
                autocomplete="current-password"
                required
                v-model="password"
                class="appearance-none block w-full px-3 py-2 border border-divider rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
              />
            </div>
          </div>

          <div>
            <NrButton
              type="submit"
              variant="primary"
              class="w-full flex justify-center"
              :disabled="isLoading"
            >
              <template v-if="isLoading" #icon-left>
                <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </template>
              {{ isLoading ? 'Signing in...' : 'Sign in' }}
            </NrButton>
          </div>
          
          <div v-if="error" class="bg-red-500 bg-opacity-10 text-red-500 p-3 rounded">
            {{ error }}
          </div>
        </form>
      </NrCard>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useAuthStore } from '../store/auth';
import { useRouter } from 'vue-router';

const authStore = useAuthStore();
const router = useRouter();

const username = ref('');
const password = ref('');
const error = ref(null);
const isLoading = ref(false);

const handleLogin = async () => {
  isLoading.value = true;
  error.value = null;

  try {
    // Call the login method from auth store
    await authStore.login({
      username: username.value,
      password: password.value,
    });

    // Navigate to dashboard after successful login
    router.push('/dashboard');
  } catch (err) {
    // Handle login error
    error.value = err.response?.data?.detail || 'Login failed. Please check your credentials.';
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
/* Add custom styles if needed */
</style>
