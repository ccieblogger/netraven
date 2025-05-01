<template>
  <PageContainer title="Dashboard" subtitle="Overview of your network management system">
    <!-- Stats Cards (now 4 columns) -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <KpiCard label="Devices" :value="deviceStore.devices?.length ?? 0" icon="list" color="blue" />
      <KpiCard label="Jobs" :value="jobStore.jobs?.length ?? 0" icon="queue" color="primary" />
      <div class="nr-card border-l-4 border-l-gray-500 p-4 flex flex-col items-start">
        <h2 class="text-lg uppercase font-semibold text-text-secondary">SYSTEM STATUS</h2>
        <div class="mt-2 grid grid-cols-2 md:grid-cols-2 gap-2 w-full">
          <div v-for="service in services" :key="service.key" class="flex items-center space-x-2">
            <ServiceDot :status="service.status" :label="service.label" :tooltip="serviceTooltip(service)" />
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

    <!-- Device List Table Section -->
    <NrCard title="Devices" subtitle="Inventory overview" :contentClass="'pt-1 px-6 pb-6'">
      <template #header>
        <div class="px-6 pt-6">
          <div class="mb-2">
            <h2 class="text-lg font-semibold text-text-primary">Device Inventory</h2>
            <p class="text-xs text-text-secondary">Filter and search your device inventory</p>
          </div>
          <form class="bg-card rounded-t-lg px-6 py-4 flex flex-row items-center gap-x-4 w-full" @submit.prevent="handleApplyFilters">
            <label for="tag" class="sr-only">Tag</label>
            <select
              id="tag"
              v-model="selectedTag"
              class="h-10 w-48 rounded-md border-divider bg-content text-text-primary px-3 focus:border-primary focus:ring-primary"
            >
              <option value="">All Tags</option>
              <option v-for="tag in tagOptions" :key="tag.value" :value="tag.value">{{ tag.label }}</option>
            </select>
            <input
              type="text"
              v-model="searchQuery"
              placeholder="Search hostname or IP..."
              class="h-10 w-64 rounded-md border-divider bg-content text-text-primary px-3 focus:border-primary focus:ring-primary"
              aria-label="Search devices"
            />
            <button
              type="button"
              @click="handleResetFilters"
              class="h-10 px-4 rounded-md border border-divider bg-content text-text-primary hover:bg-content/80 focus:outline-none focus:ring-2 focus:ring-primary"
            >
              Reset
            </button>
            <button
              type="submit"
              class="h-10 px-4 rounded-md bg-primary text-white hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-primary"
            >
              Apply Filters
            </button>
          </form>
        </div>
      </template>
      <DeviceTable
        :devices="paginatedDevices"
        :loading="deviceStore.isLoading"
        @edit="handleEdit"
        @delete="handleDelete"
        @check-reachability="handleCheckReachability"
        @credential-check="handleCredentialCheck"
        @view-configs="handleViewConfigs"
      >
        <template #pagination>
          <PaginationControls
            :currentPage="currentPage"
            :totalPages="totalPages"
            :totalItems="filteredDevices.length"
            :pageSize="pageSize"
            @page-change="handlePageChange"
            @page-size-change="handlePageSizeChange"
          />
        </template>
      </DeviceTable>
    </NrCard>

    <DeviceFormModal
      :is-open="isFormModalOpen"
      :device-to-edit="selectedDevice"
      :backend-error="deviceStore.error"
      @close="closeFormModal"
      @save="handleSaveDevice"
    />
    <DeleteConfirmationModal
      :is-open="isDeleteModalOpen"
      item-type="device"
      :item-name="deviceToDelete?.hostname"
      @close="closeDeleteModal"
      @confirm="handleDeleteConfirm"
    />
  </PageContainer>
</template>

<script setup>
import { onMounted, ref, computed, onUnmounted } from 'vue';
import { useDeviceStore } from '../store/device';
import { useJobStore } from '../store/job';
import { useAuthStore } from '../store/auth';
import { useRouter } from 'vue-router';
import KpiCard from '../components/ui/KpiCard.vue';
import ServiceDot from '../components/ui/ServiceDot.vue';
import JobsTable from '../components/jobs-dashboard/JobsTable.vue';
import DeviceTable from '../components/DeviceTable.vue';
import ResourceFilter from '../components/ResourceFilter.vue';
import PaginationControls from '../components/PaginationControls.vue';
import DeviceFormModal from '../components/DeviceFormModal.vue';
import DeleteConfirmationModal from '../components/DeleteConfirmationModal.vue';
import { useNotificationStore } from '../store/notifications';

const deviceStore = useDeviceStore();
const jobStore = useJobStore();
const authStore = useAuthStore();
const notificationStore = useNotificationStore();
const router = useRouter();

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
  if (!authStore.isAuthenticated) return;
  isLoading.value = true;
  try {
    const url = `/api/system/status${refresh ? '?refresh=true' : ''}`;
    const token = localStorage.getItem('authToken');
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

const searchQuery = ref('');
const selectedTag = ref('');
const currentPage = ref(1);
const pageSize = ref(10);

const filteredDevices = computed(() => {
  let result = deviceStore.devices;
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase();
    result = result.filter(d =>
      d.hostname.toLowerCase().includes(q) ||
      d.ip_address.toLowerCase().includes(q)
    );
  }
  if (selectedTag.value) {
    result = result.filter(d => d.tags && d.tags.some(t => t.id === selectedTag.value));
  }
  return result;
});

const paginatedDevices = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return filteredDevices.value.slice(start, start + pageSize.value);
});

const totalPages = computed(() => Math.ceil(filteredDevices.value.length / pageSize.value));

const tagOptions = computed(() => (deviceStore.tags || []).map(t => ({ value: t.id, label: t.name })));

const isFormModalOpen = ref(false);
const selectedDevice = ref(null);
const isDeleteModalOpen = ref(false);
const deviceToDelete = ref(null);
const reachabilityLoading = ref({});

function handleEdit(device) {
  selectedDevice.value = { ...device };
  isFormModalOpen.value = true;
}
function handleDelete(device) {
  deviceToDelete.value = device;
  isDeleteModalOpen.value = true;
}
function closeFormModal() {
  isFormModalOpen.value = false;
  selectedDevice.value = null;
}
function closeDeleteModal() {
  isDeleteModalOpen.value = false;
  deviceToDelete.value = null;
}
async function handleSaveDevice(deviceData) {
  let success = false;
  try {
    if (deviceData.id) {
      success = await deviceStore.updateDevice(deviceData.id, deviceData);
    } else {
      success = await deviceStore.createDevice(deviceData);
    }
    if (success) {
      closeFormModal();
      await deviceStore.fetchDevices();
      notificationStore.success('Device saved successfully.');
    }
  } catch (error) {
    notificationStore.error('Failed to save device.');
  }
}
async function handleDeleteConfirm() {
  if (!deviceToDelete.value) return;
  let success = false;
  try {
    success = await deviceStore.deleteDevice(deviceToDelete.value.id);
    if (success) {
      closeDeleteModal();
      await deviceStore.fetchDevices();
      notificationStore.success('Device deleted successfully.');
    }
  } catch (error) {
    closeDeleteModal();
    notificationStore.error('Failed to delete device.');
  }
}
async function handleCheckReachability(device) {
  reachabilityLoading.value[device.id] = true;
  try {
    if (!jobStore.jobs.length) {
      await jobStore.fetchJobs();
    }
    let reachJob = jobStore.jobs.find(j => j.job_type === 'reachability' && j.device_id === device.id);
    if (!reachJob && device.tags && device.tags.length > 0) {
      const deviceTagIds = device.tags.map(t => t.id);
      reachJob = jobStore.jobs.find(j => j.job_type === 'reachability' && j.tags && j.tags.some(tag => deviceTagIds.includes(tag.id)));
    }
    if (!reachJob) {
      notificationStore.error('No reachability job found for this device.');
      return;
    }
    const ok = await jobStore.runJobNow(reachJob.id);
    if (ok && jobStore.runStatus && jobStore.runStatus.data && jobStore.runStatus.data.job_id) {
      notificationStore.success('Reachability job started!');
    } else {
      notificationStore.error(jobStore.runStatus?.error || 'Failed to start reachability job');
    }
  } catch (err) {
    notificationStore.error('Failed to start reachability job');
  } finally {
    reachabilityLoading.value[device.id] = false;
  }
}
async function handleCredentialCheck(device) {
  try {
    // Find or create a credential_check job for this device
    if (!jobStore.jobs.length) {
      await jobStore.fetchJobs();
    }
    let credJob = jobStore.jobs.find(j => j.job_type === 'credential_check' && j.device_id === device.id);
    if (!credJob && device.tags && device.tags.length > 0) {
      const deviceTagIds = device.tags.map(t => t.id);
      credJob = jobStore.jobs.find(j => j.job_type === 'credential_check' && j.tags && j.tags.some(tag => deviceTagIds.includes(tag.id)));
    }
    if (!credJob) {
      // Optionally, create the job via API if not found
      notificationStore.error('No credential-check job found for this device.');
      return;
    }
    const ok = await jobStore.runJobNow(credJob.id);
    if (ok && jobStore.runStatus && jobStore.runStatus.data && jobStore.runStatus.data.job_id) {
      notificationStore.success('Credential-check job started!');
    } else {
      notificationStore.error(jobStore.runStatus?.error || 'Failed to start credential-check job');
    }
  } catch (err) {
    notificationStore.error('Failed to start credential-check job');
  }
}
function handleViewConfigs(device) {
  router.push(`/backups?device_id=${device.id}`);
}
function handleFilterChange(filters) {
  selectedTag.value = filters.tag || '';
  currentPage.value = 1;
}
function handleSearchInput(e) {
  searchQuery.value = e.target.value;
  currentPage.value = 1;
}
function handlePageChange(page) {
  currentPage.value = page;
}
function handlePageSizeChange(size) {
  pageSize.value = size;
  currentPage.value = 1;
}
function handleApplyFilters() {
  handleFilterChange({ tag: selectedTag });
}
function handleResetFilters() {
  selectedTag.value = '';
  searchQuery.value = '';
  handleFilterChange({ tag: '' });
}

onMounted(() => {
  if (authStore.isAuthenticated) {
    fetchSystemStatus();
  }
  startPolling();
  deviceStore.fetchDevices();
  jobStore.fetchJobs();

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
