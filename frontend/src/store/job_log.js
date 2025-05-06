import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../services/api'

export const useJobLogStore = defineStore('job_logs', () => {
  const logs = ref([])
  const isLoading = ref(false)
  const error = ref(null)
  const jobNames = ref([])
  const deviceNames = ref([])
  const jobNamesLoading = ref(false)
  const deviceNamesLoading = ref(false)
  const jobNamesError = ref(null)
  const deviceNamesError = ref(null)
  const filters = ref({
    search: '',
    job_name: null,
    device_names: [],
    job_type: null,
    level: null
  })
  const pagination = ref({
      currentPage: 1,
      itemsPerPage: 20,
      totalItems: 0,
      totalPages: 0,
  })

  const totalPages = computed(() => pagination.value.totalPages)

  async function fetchJobNames() {
    jobNamesLoading.value = true
    jobNamesError.value = null
    try {
      // No /logs/job-names endpoint; fetch logs and extract unique job names client-side
      const response = await api.get('/logs/', { params: { size: 1000 } })
      const items = response.data.items || response.data || []
      jobNames.value = [...new Set(items.map(l => l.job_name).filter(Boolean))]
    } catch (err) {
      jobNamesError.value = err.response?.data?.detail || 'Failed to fetch job names'
      jobNames.value = []
    } finally {
      jobNamesLoading.value = false
    }
  }

  async function fetchDeviceNames() {
    deviceNamesLoading.value = true
    deviceNamesError.value = null
    try {
      const response = await api.get('/devices/')
      console.log('Device fetch response:', response.data)
      const items = response.data.items || response.data || []
      deviceNames.value = items.map(d => d.hostname)
    } catch (err) {
      deviceNamesError.value = err.response?.data?.detail || 'Failed to fetch device names'
      deviceNames.value = []
    } finally {
      deviceNamesLoading.value = false
    }
  }

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
      // Convert device_names to comma-separated string for API if it's an array
      if (params.device_names) {
        if (Array.isArray(params.device_names)) {
          params.device_names = params.device_names.join(',');
        }
        // If it's an empty string or array, remove the param
        if (params.device_names === '' || params.device_names.length === 0) {
          delete params.device_names;
        }
      }
      Object.keys(params).forEach(key => (params[key] == null || params[key] === '' || (Array.isArray(params[key]) && params[key].length === 0)) && delete params[key])
      const response = await api.get('/logs/', { params })
      if (response.data && Array.isArray(response.data.items)) {
        logs.value = response.data.items
        pagination.value.totalItems = response.data.total
        pagination.value.totalPages = response.data.pages
        pagination.value.currentPage = response.data.page
        pagination.value.itemsPerPage = response.data.size
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
    filters.value = {
      search: '',
      job_name: null,
      device_names: [],
      job_type: null,
      level: null
    }
    resetPagination()
    pagination.value.itemsPerPage = 20
  }

  return {
    logs, isLoading, error, filters, pagination, totalPages, fetchLogs, $reset,
    jobNames, deviceNames, jobNamesLoading, deviceNamesLoading, jobNamesError, deviceNamesError,
    fetchJobNames, fetchDeviceNames
  }
}) 