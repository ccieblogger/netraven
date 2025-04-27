<template>
  <PageContainer title="Dashboard" subtitle="Overview of your network management system">
    <!-- Stats Cards (now 4 columns) -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <KpiCard label="Devices" :value="deviceStore.devices?.length ?? 0" icon="list" color="blue" />
      <KpiCard label="Jobs" :value="jobStore.jobs?.length ?? 0" icon="queue" color="primary" />
      <KpiCard label="Backups" :value="backupStore.backups ?? 0" icon="memory" color="green" />
      <div class="nr-card border-l-4 border-l-gray-500 p-4 flex flex-col items-start">
        <h2 class="text-lg uppercase font-semibold text-text-secondary">SYSTEM STATUS</h2>
        <div class="mt-2 grid grid-cols-2 md:grid-cols-2 gap-2 w-full">
          <div v-for="service in services" :key="service.key" class="flex items-center space-x-2">
            <StatusBadge :status="service.status" :label="service.label" />
          </div>
        </div>
        <div class="border-t border-divider px-4 py-2 flex justify-between items-center text-xs text-text-secondary w-full mt-2">
          <span>Last checked: {{ lastCheckedDisplay }}</span>
          <span>
            Auto-refresh in: {{ countdown }}s
            <a href="#" @click.prevent="manualRefresh" class="ml-2 text-blue-500 hover:underline" :aria-label="'Refresh system status'" :disabled="isLoading">Refresh now</a>
          </span>
        </div>
      </div>
    </div>

    <!-- Recent Jobs Section -->
    <NrCard title="Recent Jobs" subtitle="Latest job runs">
      <template #header>
        <div class="flex justify-between items-center">
          <div>
            <h2 class="text-lg font-semibold text-text-primary">Recent Jobs</h2>
            <p class="text-xs text-text-secondary">Latest job runs</p>
          </div>
          <router-link to="/jobs" class="flex items-center text-sm font-medium text-primary hover:text-primary-light">
            View All Jobs
            <svg class="ml-1 w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </router-link>
        </div>
      </template>
      <JobsTable :activeTab="'recent'" :recentJobs="jobStore.jobs.slice(0, 5)" />
    </NrCard>
  </PageContainer>
</template>

<script setup>
import { onMounted, ref, computed, onUnmounted } from 'vue';
import { useDeviceStore } from '../store/device';
import { useJobStore } from '../store/job';
import { useBackupStore } from '../store/backup';
import KpiCard from '../components/ui/KpiCard.vue';
import StatusBadge from '../components/ui/StatusBadge.vue';
import JobsTable from '../components/jobs-dashboard/JobsTable.vue';

const deviceStore = useDeviceStore();
const jobStore = useJobStore();
const backupStore = useBackupStore();

// --- System Status Card State ---
const services = ref([
  { key: 'api', label: 'API', status: 'unknown' },
  { key: 'postgres', label: 'PostgreSQL', status: 'unknown' },
  { key: 'redis', label: 'Redis', status: 'unknown' },
  { key: 'worker', label: 'Worker', status: 'unknown' },
  { key: 'scheduler', label: 'Scheduler', status: 'unknown' },
]);
const isLoading = ref(false);
const lastChecked = ref(null);
const countdown = ref(30);
let intervalId = null;
let countdownId = null;

function serviceTooltip(service) {
  if (service.status === 'healthy') return 'Healthy';
  if (service.status === 'unhealthy') return 'Unhealthy';
  return 'Unknown';
}

function updateServicesStatus(statusObj) {
  services.value.forEach(s => {
    s.status = statusObj[s.key] || 'unknown';
  });
}

async function fetchSystemStatus(refresh = false) {
  isLoading.value = true;
  try {
    const url = `/api/system/status${refresh ? '?refresh=true' : ''}`;
    const token = localStorage.getItem('access_token');
    const res = await fetch(url, {
      headers: token ? { 'Authorization': `Bearer ${token}` } : {}
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    const data = await res.json();
    updateServicesStatus(data);
    lastChecked.value = new Date();
  } catch (e) {
    console.error("Failed to fetch system status:", e);
    services.value.forEach(s => (s.status = 'unknown'));
  } finally {
    isLoading.value = false;
    countdown.value = 30;
  }
}

function manualRefresh() {
  fetchSystemStatus(true);
}

const lastCheckedDisplay = computed(() => {
  if (!lastChecked.value) return 'Never';
  return lastChecked.value.toLocaleTimeString();
});

function startPolling() {
  intervalId = setInterval(() => {
    fetchSystemStatus();
  }, 30000);
  countdownId = setInterval(() => {
    if (countdown.value > 0) countdown.value--;
  }, 1000);
}
function stopPolling() {
  if (intervalId) clearInterval(intervalId);
  if (countdownId) clearInterval(countdownId);
}

// Simulated data for recent activity
const recentLogs = ref([]);

onMounted(() => {
  fetchSystemStatus();
  startPolling();
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
  }, 1500);
});
onUnmounted(() => {
  stopPolling();
});
</script>
