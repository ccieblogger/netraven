<template>
  <PageContainer title="Dashboard" subtitle="Overview of your network management system">
    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <!-- Devices Card -->
      <NrCard className="border-l-4 border-l-blue-500">
        <div class="p-4 flex justify-between items-start">
          <div>
            <h2 class="text-lg uppercase font-semibold text-text-secondary">DEVICES</h2>
            <div class="mt-2 flex items-baseline">
              <p class="text-4xl font-bold text-text-primary">{{ deviceStore.devices?.length ?? 0 }}</p>
              <p class="ml-2 text-sm text-text-secondary">Total Managed Devices</p>
            </div>
          </div>
          <div class="flex items-center justify-center h-10 w-10 rounded-md bg-blue-600">
            <svg class="w-6 h-6 text-blue-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
              <line x1="8" y1="21" x2="16" y2="21" />
              <line x1="12" y1="17" x2="12" y2="21" />
            </svg>
          </div>
        </div>
        <div class="border-t border-divider px-4 py-3">
          <router-link to="/devices" class="flex items-center text-sm font-medium text-blue-400 hover:text-primary">
            View Devices
            <svg class="ml-1 w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </router-link>
        </div>
      </NrCard>

      <!-- Jobs Card -->
      <NrCard className="border-l-4 border-l-primary">
        <div class="p-4 flex justify-between items-start">
          <div>
            <h2 class="text-lg uppercase font-semibold text-text-secondary">JOBS</h2>
            <div class="mt-2 flex items-baseline">
              <p class="text-4xl font-bold text-text-primary">{{ jobStore.jobs?.length ?? 0 }}</p>
              <p class="ml-2 text-sm text-text-secondary">Active Jobs</p>
            </div>
          </div>
          <div class="flex items-center justify-center h-10 w-10 rounded-md bg-primary-dark">
            <svg class="w-6 h-6 text-primary-light" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3.332.8-4.5 2.05C10.875 3.87 9.32 3 7.5 3A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
            </svg>
          </div>
        </div>
        <div class="border-t border-divider px-4 py-3">
          <router-link to="/jobs" class="flex items-center text-sm font-medium text-primary hover:text-primary-light">
            View Jobs
            <svg class="ml-1 w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </router-link>
        </div>
      </NrCard>

      <!-- Credentials Card -->
      <NrCard className="border-l-4 border-l-purple-600">
        <div class="p-4 flex justify-between items-start">
          <div>
            <h2 class="text-lg uppercase font-semibold text-text-secondary">CREDENTIALS</h2>
            <div class="mt-2 flex items-baseline">
              <p class="text-4xl font-bold text-text-primary">{{ credentialStore.credentials?.length ?? 0 }}</p>
              <p class="ml-2 text-sm text-text-secondary">Stored Credentials</p>
            </div>
          </div>
          <div class="flex items-center justify-center h-10 w-10 rounded-md bg-purple-700">
            <svg class="w-6 h-6 text-purple-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path d="M15 7a2 2 0 0 1 2 2m4 0a6 6 0 0 1-7.743 5.743L11 17H9v2H7v2H4a1 1 0 0 1-1-1v-2.586a1 1 0 0 1 .293-.707l5.964-5.964A6 6 0 0 1 21 9z" />
            </svg>
          </div>
        </div>
        <div class="border-t border-divider px-4 py-3">
          <router-link to="/credentials" class="flex items-center text-sm font-medium text-purple-400 hover:text-purple-300">
            View Credentials
            <svg class="ml-1 w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </router-link>
        </div>
      </NrCard>
    </div>
  </PageContainer>
</template>

<script setup>
import { onMounted } from 'vue';
import { useDeviceStore } from '../store/device';
import { useJobStore } from '../store/job';
import { useCredentialStore } from '../store/credential';

// Initialize stores
const deviceStore = useDeviceStore();
const jobStore = useJobStore();
const credentialStore = useCredentialStore();

// Fetch data on component mount
onMounted(() => {
  deviceStore.fetchDevices();
  jobStore.fetchJobs();
  credentialStore.fetchCredentials();
});
</script>
