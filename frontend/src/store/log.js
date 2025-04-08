import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export const useLogStore = defineStore('logs', () => {
  const logs = ref([])
  const isLoading = ref(false)
  const error = ref(null)
  const filters = ref({ job_id: null, device_id: null, log_type: null }) // Store filters
  const pagination = ref({ skip: 0, limit: 100, total: 0 }) // Add pagination state if needed

  async function fetchLogs(newFilters = {}) {
    isLoading.value = true
    error.value = null
    // Update filters
    filters.value = { ...filters.value, ...newFilters };
    
    try {
      const params = {
        skip: pagination.value.skip,
        limit: pagination.value.limit,
        ...filters.value // Add current filters
      };
      // Remove null filters
      Object.keys(params).forEach(key => params[key] == null && delete params[key]);

      const response = await api.get('/logs', { params })
      logs.value = response.data
      // Optionally update total count if API provides it for pagination
      // pagination.value.total = response.headers['x-total-count'] || response.data.length;
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch logs'
      console.error("Fetch Logs Error:", err)
      logs.value = [] // Clear logs on error
    } finally {
      isLoading.value = false
    }
  }
  
  // Action to change page or limit
  // async function changePage(newSkip, newLimit) {
  //   pagination.value.skip = newSkip;
  //   if (newLimit) pagination.value.limit = newLimit;
  //   await fetchLogs();
  // }

  function $reset() {
    logs.value = []
    isLoading.value = false
    error.value = null
    filters.value = { job_id: null, device_id: null, log_type: null }
    pagination.value = { skip: 0, limit: 100, total: 0 }
  }

  return { logs, isLoading, error, filters, pagination, fetchLogs, $reset }
}) 