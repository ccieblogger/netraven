<template>
  <div class="flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 sm:px-6">
    <!-- Mobile version -->
    <div class="flex flex-1 justify-between sm:hidden">
      <button
        @click="changePage(currentPage - 1)"
        :disabled="currentPage <= 1"
        class="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Previous
      </button>
      <span class="mx-2 text-sm text-gray-700">
        {{ currentPage }} / {{ totalPages }}
      </span>
      <button
        @click="changePage(currentPage + 1)"
        :disabled="currentPage >= totalPages"
        class="relative ml-3 inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Next
      </button>
    </div>

    <!-- Desktop version -->
    <div class="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
      <!-- Info text -->
      <div>
        <p class="text-sm text-gray-700">
          Showing
          <span class="font-medium">{{ startItem }}</span>
          to
          <span class="font-medium">{{ endItem }}</span>
          of
          <span class="font-medium">{{ totalItems }}</span>
          results
        </p>
      </div>

      <!-- Page size selector -->
      <div class="mr-4" v-if="showPageSizeSelector">
        <label for="page-size" class="sr-only">Items per page</label>
        <select
          id="page-size"
          v-model="localPageSize"
          class="rounded-md border-gray-300 py-1 pl-2 pr-8 text-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500"
        >
          <option v-for="size in pageSizes" :key="size" :value="size">
            {{ size }} per page
          </option>
        </select>
      </div>

      <!-- Pagination navigation -->
      <div>
        <nav class="isolate inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
          <!-- First page -->
          <button
            v-if="showFirstLastButtons"
            @click="changePage(1)"
            :disabled="currentPage <= 1"
            class="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span class="sr-only">First</span>
            <ChevronDoubleLeftIcon class="h-5 w-5" aria-hidden="true" />
          </button>

          <!-- Previous -->
          <button
            @click="changePage(currentPage - 1)"
            :disabled="currentPage <= 1"
            class="relative inline-flex items-center px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50 disabled:cursor-not-allowed"
            :class="{ 'rounded-l-md': !showFirstLastButtons }"
          >
            <span class="sr-only">Previous</span>
            <ChevronLeftIcon class="h-5 w-5" aria-hidden="true" />
          </button>

          <!-- Page numbers -->
          <template v-if="showPageNumbers">
            <button
              v-for="page in displayedPageNumbers"
              :key="page"
              @click="changePage(page)"
              :class="[
                'relative inline-flex items-center px-4 py-2 text-sm ring-1 ring-inset focus:z-20',
                page === currentPage
                  ? 'z-10 bg-indigo-600 text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600'
                  : 'text-gray-900 ring-inset ring-gray-300 hover:bg-gray-50 focus:outline-offset-0',
                page === '...' ? 'pointer-events-none' : ''
              ]"
              :disabled="page === '...'"
            >
              {{ page }}
            </button>
          </template>

          <!-- Simple page indicator if not showing numbers -->
          <span
            v-else
            class="relative inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-700 ring-1 ring-inset ring-gray-300"
          >
            {{ currentPage }} / {{ totalPages }}
          </span>

          <!-- Next -->
          <button
            @click="changePage(currentPage + 1)"
            :disabled="currentPage >= totalPages"
            class="relative inline-flex items-center px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50 disabled:cursor-not-allowed"
            :class="{ 'rounded-r-md': !showFirstLastButtons }"
          >
            <span class="sr-only">Next</span>
            <ChevronRightIcon class="h-5 w-5" aria-hidden="true" />
          </button>

          <!-- Last page -->
          <button
            v-if="showFirstLastButtons"
            @click="changePage(totalPages)"
            :disabled="currentPage >= totalPages"
            class="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span class="sr-only">Last</span>
            <ChevronDoubleRightIcon class="h-5 w-5" aria-hidden="true" />
          </button>

          <!-- Page input -->
          <div v-if="showPageInput" class="relative ml-3 inline-flex items-center">
            <label for="page-input" class="sr-only">Go to page</label>
            <input
              id="page-input"
              v-model="pageInputValue"
              type="number"
              min="1"
              :max="totalPages"
              @keyup.enter="handlePageInputChange"
              class="block w-16 rounded-md border-gray-300 pl-2 text-sm focus:border-indigo-500 focus:ring-indigo-500"
            />
            <button
              @click="handlePageInputChange"
              class="ml-2 inline-flex items-center rounded-md border border-gray-300 bg-white px-3 py-1 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Go
            </button>
          </div>
        </nav>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { 
  ChevronLeftIcon, 
  ChevronRightIcon,
  ChevronDoubleLeftIcon,
  ChevronDoubleRightIcon
} from '@heroicons/vue/20/solid';

const props = defineProps({
  currentPage: {
    type: Number,
    required: true,
  },
  totalPages: {
    type: Number,
    required: true,
  },
  totalItems: {
    type: Number,
    required: true,
  },
  pageSize: {
    type: Number,
    default: 10,
  },
  showPageSizeSelector: {
    type: Boolean,
    default: true,
  },
  pageSizes: {
    type: Array,
    default: () => [10, 25, 50, 100],
  },
  showPageNumbers: {
    type: Boolean,
    default: true,
  },
  showFirstLastButtons: {
    type: Boolean,
    default: true,
  },
  showPageInput: {
    type: Boolean,
    default: true,
  },
  maxPageButtons: {
    type: Number,
    default: 5,
  },
});

const emit = defineEmits(['changePage', 'changePageSize']);

// Local state
const pageInputValue = ref(props.currentPage);
const localPageSize = ref(props.pageSize);

// Watch for external changes
watch(() => props.currentPage, (newVal) => {
  pageInputValue.value = newVal;
});

watch(() => props.pageSize, (newVal) => {
  localPageSize.value = newVal;
});

// Watch for local page size changes
watch(localPageSize, (newVal) => {
  if (newVal !== props.pageSize) {
    emit('changePageSize', newVal);
  }
});

// Computed properties
const startItem = computed(() => {
  if (props.totalItems === 0) return 0;
  return (props.currentPage - 1) * props.pageSize + 1;
});

const endItem = computed(() => {
  return Math.min(props.currentPage * props.pageSize, props.totalItems);
});

const displayedPageNumbers = computed(() => {
  if (props.totalPages <= props.maxPageButtons) {
    // Show all pages
    return Array.from({ length: props.totalPages }, (_, i) => i + 1);
  }

  const halfMax = Math.floor(props.maxPageButtons / 2);
  let startPage = Math.max(props.currentPage - halfMax, 1);
  let endPage = startPage + props.maxPageButtons - 1;

  if (endPage > props.totalPages) {
    endPage = props.totalPages;
    startPage = Math.max(endPage - props.maxPageButtons + 1, 1);
  }

  const pages = [];

  // Always show first page
  if (startPage > 1) {
    pages.push(1);
    if (startPage > 2) {
      pages.push('...');
    }
  }

  // Add page numbers
  for (let i = startPage; i <= endPage; i++) {
    pages.push(i);
  }

  // Always show last page
  if (endPage < props.totalPages) {
    if (endPage < props.totalPages - 1) {
      pages.push('...');
    }
    pages.push(props.totalPages);
  }

  return pages;
});

// Methods
function changePage(newPage) {
  if (newPage >= 1 && newPage <= props.totalPages) {
    pageInputValue.value = newPage;
    emit('changePage', newPage);
  }
}

function handlePageInputChange() {
  const page = parseInt(pageInputValue.value);
  if (!isNaN(page) && page >= 1 && page <= props.totalPages) {
    changePage(page);
  } else {
    // Reset to current page if invalid
    pageInputValue.value = props.currentPage;
  }
}
</script> 