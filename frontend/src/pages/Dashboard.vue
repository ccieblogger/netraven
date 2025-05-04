<template>
  <PageContainer title="Dashboard" subtitle="System overview and device inventory">
    <!-- KPI Cards Row: System Status as individual KPIs -->
    <div class="w-full px-0 mb-4">
      <div class="flex flex-row gap-4 w-full">
        <KpiCard
          v-for="service in services"
          :key="service.key"
          :label="service.label"
          :value="service.statusValue"
          icon="status"
          :color="
            service.status === 'healthy' ? 'green' :
            service.status === 'unhealthy' ? 'red' :
            'yellow'"
          :tooltip="service.tooltip"
          class="flex-1 min-w-0 h-16 w-40 max-w-xs"
        />
      </div>
    </div>

    <!-- Device List Table Section -->
    <NrCard title="Devices" subtitle="Inventory overview" :contentClass="'pt-0 px-0 pb-2'">
      <template #header>
        <div class="flex flex-row justify-between items-center w-full">
          <div class="mb-4">
            <h2 class="text-lg font-semibold text-text-primary">Device Inventory</h2>
            <p class="text-xs text-text-secondary">Filter and search your device inventory</p>
          </div>
          <form class="bg-card rounded-t-lg py-2 flex flex-row items-center gap-x-4" @submit.prevent="() => {}">
            <input
              type="text"
              v-model="searchQuery"
              placeholder="Search hostname or IP..."
              class="h-8 w-62 rounded-md border-divider bg-content text-text-primary px-3 focus:border-primary focus:ring-primary"
              aria-label="Search devices"
            />
          </form>
        </div>
      </template>
      <DeviceTable
        :devices="paginatedDevices"
        :loading="deviceStore.isLoading"
        :filters="deviceTableFilters"
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
import { onMounted, ref, computed, onUnmounted, watch } from 'vue';
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
  { key: 'api', label: 'API', status: 'unknown', statusValue: 'Unknown', tooltip: 'Not reported by backend' },
  { key: 'postgres', label: 'PostgreSQL', status: 'unknown', statusValue: 'Unknown', tooltip: 'Not reported by backend' },
  { key: 'redis', label: 'Redis', status: 'unknown', statusValue: 'Unknown', tooltip: '' },
  { key: 'worker', label: 'Worker', status: 'unknown', statusValue: 'Unknown', tooltip: '' },
  { key: 'scheduler', label: 'Scheduler', status: 'unknown', statusValue: 'Unknown', tooltip: 'Not reported by backend' },
  { key: 'rq', label: 'RQ', status: 'unknown', statusValue: 'Unknown', tooltip: '' },
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
    if (s.key === 'redis') {
      if (statusObj.redis_uptime) {
        s.status = 'healthy';
        const d = Math.floor(statusObj.redis_uptime/86400), h = Math.floor((statusObj.redis_uptime%86400)/3600);
        s.statusValue = `Up (${d}d, ${h}h)`;
        s.tooltip = '';
      } else {
        s.status = 'unknown';
        s.statusValue = 'Unknown';
        s.tooltip = 'Not reported by backend';
      }
    } else if (s.key === 'rq') {
      if (Array.isArray(statusObj.rq_queues)) {
        const totalJobs = statusObj.rq_queues.reduce((sum, q) => sum + (q.job_count || 0), 0);
        s.status = 'healthy';
        s.statusValue = totalJobs.toString();
        s.tooltip = '';
      } else {
        s.status = 'unknown';
        s.statusValue = 'Unknown';
        s.tooltip = 'Not reported by backend';
      }
    } else if (s.key === 'worker') {
      if (Array.isArray(statusObj.workers) && statusObj.workers.length > 0) {
        s.status = 'healthy';
        s.statusValue = statusObj.workers[0].status || 'Active';
        s.tooltip = '';
      } else {
        s.status = 'unknown';
        s.statusValue = 'Unknown';
        s.tooltip = 'Not reported by backend';
      }
    } else if (['api', 'postgres', 'scheduler'].includes(s.key)) {
      s.status = 'unknown';
      s.statusValue = 'Unknown';
      s.tooltip = 'Not reported by backend';
    }
  });
}

async function fetchSystemStatus(refresh = false) {
  if (!authStore.isAuthenticated) return;
  isLoading.value = true;
  try {
    // Use /jobs/status for all service KPIs
    const url = `/jobs/status`;
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
    services.value.forEach(s => {
      s.status = 'unknown';
      s.statusValue = 'Unknown';
    });
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
  return result;
});

const paginatedDevices = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return filteredDevices.value.slice(start, start + pageSize.value);
});

const totalPages = computed(() => Math.ceil(filteredDevices.value.length / pageSize.value));

const isFormModalOpen = ref(false);
const selectedDevice = ref(null);
const isDeleteModalOpen = ref(false);
const deviceToDelete = ref(null);
const reachabilityLoading = ref({});

// Add deviceTableFilters for DataTable filtering
const deviceTableFilters = ref({
  global: { value: null, matchMode: 'contains' },
  hostname: { value: null, matchMode: 'contains' },
  ip_address: { value: null, matchMode: 'contains' },
  serial: { value: null, matchMode: 'contains' },
  job_status: { value: null, matchMode: 'contains' },
});

// Optionally, wire the search box to the global filter
watch(searchQuery, (val) => {
  deviceTableFilters.value.global.value = val;
});

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
function handlePageChange(page) {
  currentPage.value = page;
}
function handlePageSizeChange(size) {
  pageSize.value = size;
  currentPage.value = 1;
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
