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
        </div>
      </template>
      <DeviceTable
        :devices="deviceStore.devices"
        :loading="loading"
        :filters="filters.value"
        :pageSize="pageSize"
        lazy
        @filter="onTableChange"
        @page="onTableChange"
        @sort="onTableChange"
        @edit="handleEdit"
        @delete="handleDelete"
        @check-reachability="handleCheckReachability"
        @credential-check="handleCredentialCheck"
        @view-configs="handleViewConfigs"
      />
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
import api from '../services/api';
import { FilterMatchMode } from 'primevue/api';

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
const filters = ref({
  global: { value: '', matchMode: FilterMatchMode.CONTAINS },
  hostname: { value: '', matchMode: FilterMatchMode.CONTAINS },
  ip_address: { value: '', matchMode: FilterMatchMode.CONTAINS },
  serial: { value: '', matchMode: FilterMatchMode.CONTAINS },
  job_status: { value: '', matchMode: FilterMatchMode.CONTAINS },
});
const first = ref(0);
const totalRecords = ref(0);
const sortField = ref(null);
const sortOrder = ref(null);
const loading = ref(false);

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

async function onTableChange(event) {
  console.log('onTableChange', event);
  // Build params for API
  const params = {};
  // Pagination
  params.page = event.first !== undefined && event.rows !== undefined
    ? Math.floor(event.first / event.rows) + 1
    : 1;
  params.size = event.rows || 10;
  // Sorting
  if (event.sortField) params.sort = event.sortField;
  if (event.sortOrder) params.order = event.sortOrder === 1 ? 'asc' : 'desc';
  // Filters
  if (event.filters) {
    Object.entries(event.filters).forEach(([key, filterObj]) => {
      if (filterObj && typeof filterObj.value === 'string' && filterObj.value.trim() !== '') {
        params[key] = filterObj.value.trim();
      }
    });
  }
  // Fetch from backend
  await deviceStore.fetchDevices(params);
}

onMounted(() => {
  if (authStore.isAuthenticated) {
    fetchSystemStatus();
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
