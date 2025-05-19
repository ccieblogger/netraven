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
      :style="'min-width:600px; max-width:900px;'"
    >
      <template #content>
        <div v-if="selectedSnapshot" class="max-h-96 overflow-y-auto">
          <div class="flex justify-between items-center mb-2">
            <div>
              <span class="text-text-secondary" style="color:#111;">Retrieved:</span> 
              <span class="text-text-primary ml-1" style="color:#111;">{{ formatDate(selectedSnapshot.retrieved_at) }}</span>
            </div>
            <div>
              <span class="text-text-secondary" style="color:#111;">Snapshot ID:</span> 
              <span class="text-text-primary ml-1" style="color:#111;">{{ selectedSnapshot.id }}</span>
            </div>
          </div>
          <pre class="p-4 rounded font-mono text-sm whitespace-pre-wrap overflow-x-auto" style="background: #111; color: #fff;">
            {{ selectedSnapshot.config_data || selectedSnapshot.snippet }}
          </pre>
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

    <!-- Diff Modal -->
    <BaseModal 
      :is-open="diffModalOpen" 
      :title="'Configuration Diff'"
      @close="closeDiffModal"
    >
      <template #content>
        <DiffViewer
          v-if="diffModalOpen"
          :oldContent="diffOldSnapshot?.config_data || ''"
          :newContent="diffNewSnapshot?.config_data || ''"
          :oldVersion="diffOldSnapshot"
          :newVersion="diffNewSnapshot"
          :diff="diffResult"
          :isLoading="diffLoading"
          :error="diffError"
        />
        <p v-else class="text-text-secondary">No diff data available.</p>
      </template>
      
      <template #actions>
        <button
          @click="closeDiffModal"
          class="px-4 py-2 border border-divider text-text-secondary rounded hover:bg-card-secondary focus:outline-none"
        >
          Close
        </button>
      </template>
    </BaseModal>

    <!-- Error Feedback -->
    <div v-if="errorMsg" class="text-red-600">{{ errorMsg }}</div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { ArrowPathIcon } from '@heroicons/vue/24/solid';
import BaseModal from '../components/BaseModal.vue';
import SearchBar from '../components/backups/SearchBar.vue';
import SnapshotsTable from '../components/backups/SnapshotsTable.vue';
import DiffViewer from '../components/DiffViewer.vue';
import * as configSnapshotsService from '../services/configSnapshotsService';
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
  sort: null
});
const viewModalOpen = ref(false);
const selectedSnapshot = ref(null);
const diffModalOpen = ref(false);
const diffOldSnapshot = ref(null);
const diffNewSnapshot = ref(null);
const diffLoading = ref(false);
const diffError = ref('');
const diffResult = ref('');
const diffParams = reactive({ deviceId: '', v1: '', v2: '' });
const downloadLoading = ref(false);
const errorMsg = ref('');

// Lifecycle hooks
onMounted(() => {
  loadSnapshots();
  fetchDevices();
});

// Methods
async function loadSnapshots() {
  isLoading.value = true;
  try {
    // If a search query is present, use /configs/search, else use /configs (paginated)
    const hasQuery = filters.query && filters.query.trim();
    let data;
    if (hasQuery) {
      // Always send a non-empty q param for /configs/search
      const resp = await configSnapshotsService.searchSnapshots({ query: filters.query });
      // /configs/search returns an array, not paginated
      data = { items: resp.data, total: resp.data.length, total_pages: 1 };
    } else {
      // Use paginated list endpoint
      const resp = await configSnapshotsService.listSnapshots({
        deviceId: filters.deviceId,
        page: pagination.currentPage,
        perPage: pagination.perPage
      });
      // /configs returns paginated data (array)
      data = {
        items: resp.data,
        total: resp.data.length,
        total_pages: 1
      };
    }
    // Map device_name and snippet for table display
    snapshots.value = (data.items || []).map(snap => {
      // Try config_metadata.hostname, else lookup from devices list, else fallback
      let deviceName = snap.config_metadata?.hostname;
      if (!deviceName && devices.value.length && snap.device_id) {
        const found = devices.value.find(d => d.id === snap.device_id);
        deviceName = found ? found.name || found.hostname : undefined;
      }
      if (!deviceName) deviceName = snap.device_name || snap.device_id;
      // Snippet: use API snippet, else generate from config_data
      let snippet = snap.snippet;
      if (!snippet && snap.config_data) {
        const lines = snap.config_data.split('\n').slice(0, 2).join(' ');
        snippet = lines.length > 0 ? lines + (snap.config_data.split('\n').length > 2 ? ' ...' : '') : '';
      }
      return {
        ...snap,
        device_name: deviceName,
        snippet
      };
    });
    pagination.total = data.total || 0;
    pagination.totalPages = data.total_pages || 1;
  } catch (err) {
    console.error('Failed to load snapshots', err);
    errorMsg.value = 'Failed to load snapshots.';
  } finally {
    isLoading.value = false;
  }
}

async function fetchDevices() {
  try {
    // Use trailing slash and expect paginated response
    const response = await api.get('/devices/', { params: { page: 1, size: 100 } });
    devices.value = response.data.items || [];
  } catch (error) {
    console.error('Failed to fetch devices:', error);
    errorMsg.value = 'Failed to fetch devices.';
  }
}

function handleSearch(newFilters) {
  Object.assign(filters, newFilters);
  pagination.currentPage = 1;
  loadSnapshots();
}

function handleSort(sort) {
  sorting.sort = sort;
  loadSnapshots();
}

function handlePageChange(page) {
  pagination.currentPage = page;
  loadSnapshots();
}

function refreshData() {
  loadSnapshots();
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
async function handleViewSnapshot(snapshot) {
  try {
    isLoading.value = true;
    const { data } = await configSnapshotsService.getSnapshot(snapshot.id);
    selectedSnapshot.value = data;
    viewModalOpen.value = true;
  } catch (err) {
    errorMsg.value = 'Failed to load snapshot.';
    console.error(err);
  } finally {
    isLoading.value = false;
  }
}

function closeViewModal() {
  viewModalOpen.value = false;
  selectedSnapshot.value = null;
}

async function handleDiffSnapshot({ deviceId, v1, v2 }) {
  diffModalOpen.value = true;
  diffLoading.value = true;
  diffError.value = '';
  diffResult.value = '';
  diffParams.deviceId = deviceId;
  diffParams.v1 = v1;
  diffParams.v2 = v2;
  try {
    // Fetch both snapshots for context (for version info)
    const [oldSnap, newSnap, diffResp] = await Promise.all([
      configSnapshotsService.getSnapshot(deviceId, v1),
      configSnapshotsService.getSnapshot(deviceId, v2),
      configSnapshotsService.getDiff(deviceId, v1, v2)
    ]);
    diffOldSnapshot.value = oldSnap.data;
    diffNewSnapshot.value = newSnap.data;
    diffResult.value = diffResp.data;
  } catch (err) {
    diffError.value = 'Failed to load diff data.';
  } finally {
    diffLoading.value = false;
  }
}

function closeDiffModal() {
  diffModalOpen.value = false;
  diffOldSnapshot.value = null;
  diffNewSnapshot.value = null;
  diffResult.value = '';
  diffError.value = '';
}

async function handleDownloadSnapshot(snapshot) {
  try {
    downloadLoading.value = true;
    const response = await configSnapshotsService.downloadSnapshot(snapshot.id);
    // If response.data is an object, extract config_data
    const configText = response.data.config_data || response.data;
    const url = window.URL.createObjectURL(new Blob([configText], { type: 'text/plain' }));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `config_snapshot_${snapshot.id}.txt`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  } catch (err) {
    errorMsg.value = 'Failed to download snapshot.';
    console.error(err);
  } finally {
    downloadLoading.value = false;
  }
}
</script>