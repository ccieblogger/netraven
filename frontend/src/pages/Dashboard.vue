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

      <!-- Backups Card -->
      <NrCard className="border-l-4 border-l-green-600">
        <div class="p-4 flex justify-between items-start">
          <div>
            <h2 class="text-lg uppercase font-semibold text-text-secondary">BACKUPS</h2>
            <div class="mt-2 flex items-baseline">
              <p class="text-4xl font-bold text-text-primary">{{ backupStore.backups ?? 0 }}</p>
              <p class="ml-2 text-sm text-text-secondary">Stored Backup Files</p>
            </div>
          </div>
          <div class="flex items-center justify-center h-10 w-10 rounded-md bg-green-700">
            <svg class="w-6 h-6 text-green-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path d="M12 4v16m8-8H4" />
            </svg>
          </div>
        </div>
        <div class="border-t border-divider px-4 py-3">
          <router-link to="/backups" class="flex items-center text-sm font-medium text-green-400 hover:text-green-300">
            View Backups
            <svg class="ml-1 w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </router-link>
        </div>
      </NrCard>
    </div>

    <!-- Recent Activity Section -->
    <NrCard title="Recent Activity" subtitle="Latest system events and logs">
      <template #header>
        <div class="flex justify-between items-center">
          <div>
            <h2 class="text-lg font-semibold text-text-primary">Recent Activity</h2>
            <p class="text-xs text-text-secondary">Latest system events and logs</p>
          </div>
          <router-link to="/logs" class="flex items-center text-sm font-medium text-primary hover:text-primary-light">
            View All Logs
            <svg class="ml-1 w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </router-link>
        </div>
      </template>
      
      <div v-if="isLoading" class="flex justify-center items-center py-6">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <span class="ml-3 text-text-secondary">Loading recent activity...</span>
      </div>
      <div v-else-if="recentLogs.length === 0" class="py-6 text-center">
        <p class="text-text-secondary">No recent activity found</p>
      </div>
      <div v-else class="divide-y divide-divider">
        <div v-for="(log, index) in recentLogs" :key="index" class="py-3 px-4">
          <div class="flex justify-between">
            <span class="text-text-primary font-medium">{{ log.title }}</span>
            <span class="text-text-secondary text-sm">{{ log.timestamp }}</span>
          </div>
          <p class="text-text-secondary text-sm mt-1">{{ log.message }}</p>
        </div>
      </div>
    </NrCard>
  </PageContainer>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { useDeviceStore } from '../store/device';
import { useJobStore } from '../store/job';
import { useBackupStore } from '../store/backup'; // Import the backup store

// Initialize stores
const deviceStore = useDeviceStore();
const jobStore = useJobStore();
const backupStore = useBackupStore(); // Initialize the backup store

// Simulated data for recent activity
const isLoading = ref(true);
const recentLogs = ref([]);

// Fetch data on component mount
onMounted(() => {
  deviceStore.fetchDevices();
  jobStore.fetchJobs();
  backupStore.fetchBackups();

  // Simulate loading delay for recent activity
  setTimeout(() => {
    recentLogs.value = [
      { 
        title: 'Config Backup Complete', 
        message: 'Successfully backed up configurations for 12 devices',
        timestamp: '10 minutes ago'
      },
      { 
        title: 'New Device Added', 
        message: 'Added device core-sw-01 to the inventory',
        timestamp: '2 hours ago'
      },
      { 
        title: 'Job Failed', 
        message: 'Config deployment job failed on edge-rtr-02',
        timestamp: '4 hours ago'
      }
    ];
    isLoading.value = false;
  }, 1500);
});
</script>
