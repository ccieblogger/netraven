<template>
  <div class="overflow-x-auto">
    <table class="min-w-full divide-y divide-divider">
      <thead class="bg-card-secondary">
        <tr>
          <th
            v-for="column in columns"
            :key="column.key"
            :class="[
              'px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider',
              column.sortable ? 'cursor-pointer hover:text-text-primary' : '',
              column.class || ''
            ]"
            @click="column.sortable ? sort(column.key) : null"
          >
            <div class="flex items-center">
              {{ column.label }}
              <span v-if="column.sortable" class="ml-1">
                <ChevronUpIcon 
                  v-if="sortKey === column.key && sortOrder === 'asc'"
                  class="w-4 h-4 text-primary" 
                />
                <ChevronDownIcon 
                  v-else-if="sortKey === column.key && sortOrder === 'desc'"
                  class="w-4 h-4 text-primary" 
                />
                <ArrowsUpDownIcon 
                  v-else
                  class="w-4 h-4 text-text-tertiary" 
                />
              </span>
            </div>
          </th>
        </tr>
      </thead>
      <tbody class="bg-card divide-y divide-divider">
        <tr v-if="loading" class="animate-pulse">
          <td :colspan="columns.length" class="px-6 py-4">
            <div class="flex items-center justify-center">
              <ArrowPathIcon class="w-5 h-5 text-text-secondary animate-spin" />
              <span class="ml-2 text-text-secondary">Loading...</span>
            </div>
          </td>
        </tr>
        <tr v-else-if="snapshots.length === 0">
          <td :colspan="columns.length" class="px-6 py-10 text-center text-text-secondary">
            No configuration snapshots found
          </td>
        </tr>
        <tr 
          v-for="snapshot in snapshots" 
          :key="snapshot.id" 
          class="hover:bg-card-secondary"
        >
          <td class="px-6 py-4 whitespace-nowrap text-sm text-text-primary">
            {{ snapshot.device_name }}
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-text-primary">
            {{ snapshot.id }}
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-text-secondary">
            {{ formatDate(snapshot.retrieved_at) }}
          </td>
          <td class="px-6 py-4 text-sm text-text-primary max-w-xs truncate">
            <code class="font-mono text-xs bg-card-secondary p-1 rounded">
              {{ snapshot.snippet }}
            </code>
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-text-secondary flex gap-2">
            <button @click="viewSnapshot(snapshot)" class="text-primary underline bg-transparent border-0 p-0 m-0 cursor-pointer focus:outline-none">View</button>
            <router-link
              v-if="getPreviousSnapshotId(snapshot)"
              :to="{
                path: '/backups/diff',
                query: {
                  deviceId: snapshot.device_id,
                  v1: getPreviousSnapshotId(snapshot),
                  v2: snapshot.id
                }
              }"
              class="text-primary underline bg-transparent border-0 p-0 m-0 cursor-pointer focus:outline-none"
              >Diff</router-link>
            <button v-else disabled class="text-text-tertiary underline bg-transparent border-0 p-0 m-0 cursor-not-allowed">Diff</button>
            <button @click="downloadSnapshot(snapshot)" class="text-primary underline bg-transparent border-0 p-0 m-0 cursor-pointer focus:outline-none">Download</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
  <div class="px-4 py-3 bg-card border-t border-divider sm:px-6">
    <div class="flex items-center justify-between">
      <div class="flex items-center">
        <span class="text-sm text-text-secondary">
          Showing
          <span class="font-medium">{{ paginationStart }}</span>
          to
          <span class="font-medium">{{ paginationEnd }}</span>
          of
          <span class="font-medium">{{ totalSnapshots }}</span>
          results
        </span>
      </div>
      <div>
        <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
          <button
            @click="prevPage"
            :disabled="page === 1"
            :class="[
              'relative inline-flex items-center px-2 py-2 rounded-l-md border border-divider bg-card',
              page === 1 ? 'text-text-tertiary cursor-not-allowed' : 'text-text-secondary hover:bg-card-secondary'
            ]"
          >
            <span class="sr-only">Previous</span>
            <ChevronLeftIcon class="h-5 w-5" aria-hidden="true" />
          </button>
          <button
            @click="nextPage"
            :disabled="page === totalPages"
            :class="[
              'relative inline-flex items-center px-2 py-2 rounded-r-md border border-divider bg-card',
              page === totalPages ? 'text-text-tertiary cursor-not-allowed' : 'text-text-secondary hover:bg-card-secondary'
            ]"
          >
            <span class="sr-only">Next</span>
            <ChevronRightIcon class="h-5 w-5" aria-hidden="true" />
          </button>
        </nav>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { 
  Menu, 
  MenuButton, 
  MenuItem, 
  MenuItems 
} from '@headlessui/vue';
import { 
  ChevronUpIcon, 
  ChevronDownIcon, 
  ChevronLeftIcon,
  ChevronRightIcon,
  ArrowPathIcon,
  ArrowsUpDownIcon,
  EyeIcon,
  ArrowsRightLeftIcon,
  ArrowDownTrayIcon
} from '@heroicons/vue/24/solid';
import { useRouter } from 'vue-router';

// Props
const props = defineProps({
  snapshots: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  page: {
    type: Number,
    default: 1
  },
  perPage: {
    type: Number,
    default: 10
  },
  totalSnapshots: {
    type: Number,
    default: 0
  }
});

// Emits
const emit = defineEmits(['view', 'diff', 'download', 'sort', 'page-change']);

// State
const sortKey = ref('retrieved_at');
const sortOrder = ref('desc'); // Default sorting: newest first

// Table columns definition
const columns = [
  { key: 'device_name', label: 'Device', sortable: true },
  { key: 'id', label: 'Snapshot ID', sortable: true },
  { key: 'retrieved_at', label: 'Retrieved At', sortable: true },
  { key: 'snippet', label: 'Snippet', sortable: false, class: 'max-w-xs' },
  { key: 'actions', label: 'Actions', sortable: false, class: 'w-24' }
];

// Computed
const totalPages = computed(() => {
  return Math.ceil(props.totalSnapshots / props.perPage) || 1;
});

const paginationStart = computed(() => {
  return (props.page - 1) * props.perPage + 1;
});

const paginationEnd = computed(() => {
  return Math.min(props.page * props.perPage, props.totalSnapshots);
});

// Methods
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

function viewSnapshot(snapshot) {
  emit('view', snapshot);
}

function diffSnapshot(snapshot) {
  emit('diff', snapshot);
}

function downloadSnapshot(snapshot) {
  emit('download', snapshot);
}

function sort(key) {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey.value = key;
    sortOrder.value = 'asc';
  }
  
  emit('sort', { key: sortKey.value, order: sortOrder.value });
}

function prevPage() {
  if (props.page > 1) {
    emit('page-change', props.page - 1);
  }
}

function nextPage() {
  if (props.page < totalPages.value) {
    emit('page-change', props.page + 1);
  }
}

// Helper to get previous snapshot id for diffing
function getPreviousSnapshotId(current) {
  const idx = props.snapshots.findIndex(s => s.id === current.id);
  if (idx > 0) {
    return props.snapshots[idx - 1].id;
  }
  return null;
}
</script>
