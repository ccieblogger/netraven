import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../services/api'

export const useLogStore = defineStore('logs', () => {
  const logs = ref([])
  const isLoading = ref(false)
  const error = ref(null)
  const filters = ref({ job_id: null, device_id: null, log_type: null }) // Store filters
  const pagination = ref({
      currentPage: 1,
      itemsPerPage: 20, // Default page size
      totalItems: 0,
      totalPages: 0,
  })

  // Computed property for convenience
  const totalPages = computed(() => pagination.value.totalPages);

  async function fetchLogs(page = 1, newFilters = null) {
    isLoading.value = true
    error.value = null

    // Reset page to 1 if filters change
    if (newFilters) {
        filters.value = { ...filters.value, ...newFilters };
        pagination.value.currentPage = 1; // Reset page when filters change
        page = 1; // Use page 1 for the current fetch
    } else {
        pagination.value.currentPage = page; // Update current page if only navigating
    }

    try {
        const params = {
            page: pagination.value.currentPage,
            size: pagination.value.itemsPerPage,
            ...filters.value // Add current filters
        };
        // Remove null/empty filters
        Object.keys(params).forEach(key => (params[key] == null || params[key] === '') && delete params[key]);

        console.log("Fetching logs with params:", params);
        const response = await api.get('/logs', { params })

        // Assuming API returns PaginatedResponse structure
        if (response.data && Array.isArray(response.data.items)) {
            logs.value = response.data.items;
            pagination.value.totalItems = response.data.total_items;
            pagination.value.totalPages = response.data.total_pages;
            pagination.value.currentPage = response.data.current_page;
            pagination.value.itemsPerPage = response.data.page_size; // Update size from response if needed
        } else {
            console.error("Unexpected API response format:", response.data);
            logs.value = [];
            resetPagination();
            error.value = 'Received invalid data format from server.';
        }

    } catch (err) {
        error.value = err.response?.data?.detail || 'Failed to fetch logs'
        console.error("Fetch Logs Error:", err)
        logs.value = [] // Clear logs on error
        resetPagination(); // Reset pagination on error
    } finally {
      isLoading.value = false
    }
  }

  // Helper to reset pagination state
  function resetPagination() {
      pagination.value.currentPage = 1;
      pagination.value.totalItems = 0;
      pagination.value.totalPages = 0;
      // Keep itemsPerPage as it is
  }

  function $reset() {
    logs.value = []
    isLoading.value = false
    error.value = null
    filters.value = { job_id: null, device_id: null, log_type: null }
    resetPagination(); // Use helper here
    pagination.value.itemsPerPage = 20; // Reset page size to default
  }

  // Expose totalPages computed property as well
  return { logs, isLoading, error, filters, pagination, totalPages, fetchLogs, $reset }
}) 