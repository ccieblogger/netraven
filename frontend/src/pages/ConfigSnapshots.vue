<template>
  <div class="space-y-4">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-semibold text-text-primary">Configuration Snapshots</h1>
      <button 
        @click="refreshData"
        class="flex items-center px-3 py-1.5 bg-primary text-white rounded hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-primary focus:ring-opacity-50"
      >
        <ArrowPathIcon class="w-4 h-4 mr-2" :class="{ 'animate-spin': isLoading }" />
        Refresh
      </button>
    </div>
    
    <!-- Search & Filter Bar -->
    <SearchBar 
      :devices="devices"
      :initial-search-query="filters.query"
      :initial-device-id="filters.deviceId"
      :initial-start-date="filters.startDate"
      :initial-end-date="filters.endDate"
      @search="handleSearch"
    />
    
    <!-- Snapshots Table -->
    <NrCard>
      <SnapshotsTable 
        :snapshots="snapshots"
        :loading="isLoading"
        :page="pagination.currentPage"
        :per-page="pagination.perPage"
        :total-snapshots="pagination.total"
        @view="handleViewSnapshot"
        @diff="handleDiffSnapshot"
        @download="handleDownloadSnapshot"
        @sort="handleSort"
        @page-change="handlePageChange"
      />
    </NrCard>
    
    <!-- View Snapshot Modal -->
    <BaseModal 
      :is-open="viewModalOpen" 
      :title="`Configuration: ${selectedSnapshot?.device_name || ''}`"
      @close="closeViewModal"
    >
      <template #content>
        <div v-if="selectedSnapshot" class="max-h-96 overflow-y-auto">
          <div class="flex justify-between items-center mb-2">
            <div>
              <span class="text-text-secondary">Retrieved:</span> 
              <span class="text-text-primary ml-1">{{ formatDate(selectedSnapshot.retrieved_at) }}</span>
            </div>
            <div>
              <span class="text-text-secondary">Snapshot ID:</span> 
              <span class="text-text-primary ml-1">{{ selectedSnapshot.id }}</span>
            </div>
          </div>
          <pre class="bg-card-secondary p-4 rounded font-mono text-sm whitespace-pre-wrap overflow-x-auto">{{ selectedSnapshot.snippet }}</pre>
        </div>
        <p v-else class="text-text-secondary">No configuration data available.</p>
      </template>
      
      <template #actions>
        <button
          @click="closeViewModal"
          class="px-4 py-2 border border-divider text-text-secondary rounded hover:bg-card-secondary focus:outline-none"
        >
          Close
        </button>
      </template>
    </BaseModal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { ArrowPathIcon } from '@heroicons/vue/24/solid';
import BaseModal from '../components/BaseModal.vue';
import SearchBar from '../components/backups/SearchBar.vue';
import SnapshotsTable from '../components/backups/SnapshotsTable.vue';
import { configSnapshotsService } from '../services/configSnapshots';
import api from '../services/api'; // Add this import for direct API calls

// State
const isLoading = ref(false);
const snapshots = ref([]);
const devices = ref([]); // Will be loaded from API
const filters = reactive({
  query: '',
  deviceId: null,
  startDate: null,
  endDate: null
});
const pagination = reactive({
  currentPage: 1,
  perPage: 10,
  total: 0,
  totalPages: 1
});
const sorting = reactive({
  key: 'retrieved_at',
  order: 'desc'
});
const viewModalOpen = ref(false);
const selectedSnapshot = ref(null);

// Lifecycle hooks
onMounted(() => {
  fetchDevices();
  fetchSnapshots();
});

// Methods
async function fetchSnapshots() {
  isLoading.value = true;
  try {
    // Call real API
    const response = await configSnapshotsService.search(
      filters,
      pagination.currentPage,
      pagination.perPage,
      sorting
    );
    // API returns data in response.data
    const data = response.data;
    snapshots.value = data.snapshots || [];
    pagination.total = data.pagination?.total || 0;
    pagination.totalPages = data.pagination?.total_pages || 1;
  } catch (error) {
    console.error('Failed to fetch snapshots:', error);
    // TODO: Use notification store if available
  } finally {
    isLoading.value = false;
  }
}

async function fetchDevices() {
  try {
    // Use the same pattern as Dashboard.vue: root-relative path
    const response = await api.get('/devices');
    devices.value = response.data.devices || response.data || [];
  } catch (error) {
    console.error('Failed to fetch devices:', error);
    // TODO: Use notification store if available
  }
}

function handleSearch(searchParams) {
  // Update filters from search event
  Object.assign(filters, searchParams);
  pagination.currentPage = 1; // Reset to first page on new search
  fetchSnapshots();
}

function handleSort(sortParams) {
  sorting.key = sortParams.key;
  sorting.order = sortParams.order;
  fetchSnapshots();
}

function handlePageChange(page) {
  pagination.currentPage = page;
  fetchSnapshots();
}

function refreshData() {
  fetchSnapshots();
}

function formatDate(timestamp) {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  }).format(date);
}

// Modal handlers
function handleViewSnapshot(snapshot) {
  selectedSnapshot.value = snapshot;
  viewModalOpen.value = true;
}

function closeViewModal() {
  viewModalOpen.value = false;
  selectedSnapshot.value = null;
}

function handleDiffSnapshot(snapshot) {
  // This would be implemented in a future workstream
  console.log('Diff snapshot:', snapshot);
  // In a real implementation, we would navigate to a diff view
  // router.push(`/backups/configurations/${snapshot.device_id}/${snapshot.id}/diff`);
}

function handleDownloadSnapshot(snapshot) {
  // This would be implemented in a future workstream
  console.log('Download snapshot:', snapshot);
  // In a real implementation, we would call the API to download the snapshot
  // configSnapshotsService.downloadSnapshot(snapshot.device_id, snapshot.id)
  //   .then(response => {
  //     // Create a download link and trigger it
  //     const url = window.URL.createObjectURL(new Blob([response.data]));
  //     const link = document.createElement('a');
  //     link.href = url;
  //     link.setAttribute('download', `config_${snapshot.device_name}_${snapshot.id}.txt`);
  //     document.body.appendChild(link);
  //     link.click();
  //     document.body.removeChild(link);
  //   })
  //   .catch(error => {
  //     console.error('Failed to download snapshot:', error);
  //     notificationStore.showError('Failed to download configuration snapshot');
  //   });
}
</script>