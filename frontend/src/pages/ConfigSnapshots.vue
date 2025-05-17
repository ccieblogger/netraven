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

// Lifecycle hooks
onMounted(() => {
  loadSnapshots();
  fetchDevices();
});

// Methods
async function loadSnapshots() {
  isLoading.value = true;
  try {
    const { data } = await configSnapshotsService.searchSnapshots({
      ...filters,
      page: pagination.currentPage,
      perPage: pagination.perPage,
      sort: sorting.sort
    });
    snapshots.value = data.items || [];
    pagination.total = data.total || 0;
    pagination.totalPages = data.total_pages || 1;
  } catch (err) {
    console.error('Failed to load snapshots', err);
    // TODO: Add user feedback for error
  } finally {
    isLoading.value = false;
  }
}

async function fetchDevices() {
  try {
    const response = await api.get('/devices');
    devices.value = response.data.devices || response.data || [];
  } catch (error) {
    console.error('Failed to fetch devices:', error);
    // TODO: Use notification store if available
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
function handleViewSnapshot(snapshot) {
  selectedSnapshot.value = snapshot;
  viewModalOpen.value = true;
}

function closeViewModal() {
  viewModalOpen.value = false;
  selectedSnapshot.value = null;
}

function handleDiffSnapshot(snapshot) {
  console.log('Diff snapshot:', snapshot);
}

function handleDownloadSnapshot(snapshot) {
  console.log('Download snapshot:', snapshot);
}
</script>