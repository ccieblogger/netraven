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
            <p class="text-xs text-text-secondary">Inventory of your network devices</p>
          </div>
        </div>
      </template>
      <TabGroup>
        <div class="border border-divider rounded-lg bg-card w-full">
          <TabList class="flex space-x-2 px-4 pt-4 bg-card rounded-t-lg border-b border-divider">
            <Tab v-slot="{ selected }" as="template">
              <button
                :class="[
                  'px-3 py-2 text-sm font-semibold focus:outline-none',
                  selected
                    ? 'bg-card text-text-primary border-b-2 border-white -mb-px z-10'
                    : 'text-text-secondary border-b-2 border-transparent',
                ]"
              >
                Devices
              </button>
            </Tab>
          </TabList>
          <TabPanels class="p-4">
            <TabPanel>
              <DeviceFiltersBar :filters="filters" @updateFilters="onUpdateFilters" />
              <DeviceInventoryTable
                :devices="filteredDevices"
                :loading="loading"
                :sortField="sortField"
                :sortOrder="sortOrder"
                @sort="handleSort"
                @edit="handleEdit"
                @delete="handleDelete"
                @check-reachability="handleCheckReachability"
                @credential-check="handleCredentialCheck"
                @view-configs="handleViewConfigs"
              />
            </TabPanel>
          </TabPanels>
        </div>
      </TabGroup>
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
import { onMounted, ref, computed, onUnmounted, watch, reactive } from 'vue';
import { useDeviceStore } from '../store/device';
import { useJobStore } from '../store/job';
import { useAuthStore } from '../store/auth';
import { useRouter } from 'vue-router';
import KpiCard from '../components/ui/KpiCard.vue';
import JobsTable from '../components/jobs-dashboard/JobsTable.vue';
import DeviceInventoryTable from '../components/dashboard/DeviceInventoryTable.vue';
import ResourceFilter from '../components/ResourceFilter.vue';
import PaginationControls from '../components/PaginationControls.vue';
import DeviceFormModal from '../components/DeviceFormModal.vue';
import DeleteConfirmationModal from '../components/DeleteConfirmationModal.vue';
import { useNotificationStore } from '../store/notifications';
import api from '../services/api';
import { FilterMatchMode } from 'primevue/api';
import { TabGroup, TabList, Tab, TabPanels, TabPanel } from '@headlessui/vue';
import DeviceFiltersBar from '../components/dashboard/DeviceFiltersBar.vue';

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

function capitalizeStatus(status) {
  if (!status) return 'Unknown';
  return status.charAt(0).toUpperCase() + status.slice(1).toLowerCase();
}

async function fetchSystemStatus(refresh = false) {
  if (!authStore.isAuthenticated) return;
  isLoading.value = true;
  try {
    const url = `/system/status${refresh ? '?refresh=true' : ''}`;
    const res = await api.get(url);
    const data = res.data;
    // Map system status fields to services
    services.value.forEach(s => {
      if (s.key === 'api') {
        s.status = data.api ? data.api.toLowerCase() : 'unknown';
        s.statusValue = data.api ? capitalizeStatus(data.api) : 'Unknown';
        s.tooltip = '';
      } else if (s.key === 'postgres') {
        s.status = data.postgres ? data.postgres.toLowerCase() : 'unknown';
        s.statusValue = data.postgres ? capitalizeStatus(data.postgres) : 'Unknown';
        s.tooltip = '';
      } else if (s.key === 'redis') {
        if (data.redis === 'healthy') {
          s.status = 'healthy';
          s.statusValue = 'Healthy';
          if (typeof data.redis_uptime === 'number') {
            const d = Math.floor(data.redis_uptime/86400), h = Math.floor((data.redis_uptime%86400)/3600);
            s.tooltip = `Uptime: ${d}d ${h}h`;
          } else {
            s.tooltip = '';
          }
        } else if (data.redis === 'unhealthy') {
          s.status = 'unhealthy';
          s.statusValue = 'Unhealthy';
          s.tooltip = 'Redis is unhealthy';
        } else {
          s.status = 'unknown';
          s.statusValue = 'Unknown';
          s.tooltip = 'Not reported by backend';
        }
      } else if (s.key === 'worker') {
        s.status = data.worker ? data.worker.toLowerCase() : 'unknown';
        s.statusValue = data.worker ? capitalizeStatus(data.worker) : 'Unknown';
        s.tooltip = '';
      } else if (s.key === 'scheduler') {
        s.status = data.scheduler ? data.scheduler.toLowerCase() : 'unknown';
        s.statusValue = data.scheduler ? capitalizeStatus(data.scheduler) : 'Unknown';
        s.tooltip = '';
      } else if (s.key === 'rq') {
        s.status = 'loading';
        s.statusValue = '...';
        s.tooltip = '';
      }
    });
    // Fetch RQ stats separately
    fetchRQStats();
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

async function fetchRQStats() {
  try {
    const res = await api.get('/jobs/status');
    const data = res.data;
    const rqService = services.value.find(s => s.key === 'rq');
    if (rqService) {
      if (Array.isArray(data.rq_queues) && data.rq_queues.length > 0) {
        rqService.status = 'healthy';
        rqService.statusValue = 'Healthy';
        const totalJobs = data.rq_queues.reduce((sum, q) => sum + (q.job_count || 0), 0);
        rqService.tooltip = `Total jobs in queues: ${totalJobs}`;
      } else {
        rqService.status = 'unhealthy';
        rqService.statusValue = 'Unhealthy';
        rqService.tooltip = 'No RQ queues found';
      }
    }
  } catch (e) {
    const rqService = services.value.find(s => s.key === 'rq');
    if (rqService) {
      rqService.status = 'unknown';
      rqService.statusValue = 'Unknown';
      rqService.tooltip = 'Failed to fetch RQ stats';
    }
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

const isFormModalOpen = ref(false);
const selectedDevice = ref(null);
const isDeleteModalOpen = ref(false);
const deviceToDelete = ref(null);
const reachabilityLoading = ref({});

// Add deviceTableFilters for DataTable filtering
const filters = reactive({ hostname: '', ip_address: '', serial: '', job_status: '', global: '' });
function onUpdateFilters(newFilters) {
  Object.assign(filters, newFilters);
}
const sortField = ref('hostname');
const sortOrder = ref(1); // 1 = asc, -1 = desc
function handleSort({ field, order }) {
  sortField.value = field;
  sortOrder.value = order;
}
const filteredDevices = computed(() => {
  // Simple local filtering for demo; replace with backend filtering if needed
  let result = deviceStore.devices.filter(device => {
    const matchesHostname = !filters.hostname || device.hostname?.toLowerCase().includes(filters.hostname.toLowerCase());
    const matchesIP = !filters.ip_address || device.ip_address?.includes(filters.ip_address);
    const matchesSerial = !filters.serial || device.serial?.toLowerCase().includes(filters.serial.toLowerCase());
    const matchesGlobal = !filters.global ||
      device.hostname?.toLowerCase().includes(filters.global.toLowerCase()) ||
      device.ip_address?.includes(filters.global) ||
      device.serial?.toLowerCase().includes(filters.global.toLowerCase());
    return matchesHostname && matchesIP && matchesSerial && matchesGlobal;
  });
  // Sorting
  if (sortField.value) {
    result = result.slice().sort((a, b) => {
      let aVal = a[sortField.value];
      let bVal = b[sortField.value];
      if (sortField.value === 'last_backup') {
        aVal = aVal ? new Date(aVal) : new Date(0);
        bVal = bVal ? new Date(bVal) : new Date(0);
      } else {
        aVal = aVal ? aVal.toString().toLowerCase() : '';
        bVal = bVal ? bVal.toString().toLowerCase() : '';
      }
      if (aVal < bVal) return -1 * sortOrder.value;
      if (aVal > bVal) return 1 * sortOrder.value;
      return 0;
    });
  }
  return result;
});
const first = ref(0);
const totalRecords = ref(0);
const loading = ref(false);
const pageSize = ref(10); // Default page size for DeviceTable

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

onMounted(async () => {
  if (authStore.isAuthenticated) {
    fetchSystemStatus();
    await deviceStore.fetchDevicesWithReachabilityStatus();
  }
  startPolling();
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
