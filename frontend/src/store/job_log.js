import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../services/api'

export const useJobLogStore = defineStore('job_logs', () => {
  const logs = ref([])
  const isLoading = ref(false)
  const error = ref(null)
  const filters = ref({ job_id: null, device_id: null, level: null })
  const pagination = ref({
      currentPage: 1,
      itemsPerPage: 20,
      totalItems: 0,
      totalPages: 0,
  })

  const totalPages = computed(() => pagination.value.totalPages)

  async function fetchLogs(page = 1, newFilters = null) {
    isLoading.value = true
    error.value = null
    if (newFilters) {
        filters.value = { ...filters.value, ...newFilters }
        pagination.value.currentPage = 1
        page = 1
    } else {
        pagination.value.currentPage = page
    }
    try {
        const params = {
            page: pagination.value.currentPage,
            size: pagination.value.itemsPerPage,
            ...filters.value
        }
        Object.keys(params).forEach(key => (params[key] == null || params[key] === '') && delete params[key])
        const response = await api.get('/job-logs/', { params })
        if (response.data && Array.isArray(response.data.items)) {
            logs.value = response.data.items
            pagination.value.totalItems = response.data.total_items
            pagination.value.totalPages = response.data.total_pages
            pagination.value.currentPage = response.data.current_page
            pagination.value.itemsPerPage = response.data.page_size
        } else {
            logs.value = []
            resetPagination()
            error.value = 'Received invalid data format from server.'
        }
    } catch (err) {
        error.value = err.response?.data?.detail || 'Failed to fetch job logs'
        logs.value = []
        resetPagination()
    } finally {
      isLoading.value = false
    }
  }

  function resetPagination() {
      pagination.value.currentPage = 1
      pagination.value.totalItems = 0
      pagination.value.totalPages = 0
  }

  function $reset() {
    logs.value = []
    isLoading.value = false
    error.value = null
    filters.value = { job_id: null, device_id: null, level: null }
    resetPagination()
    pagination.value.itemsPerPage = 20
  }

  return { logs, isLoading, error, filters, pagination, totalPages, fetchLogs, $reset }
}) 