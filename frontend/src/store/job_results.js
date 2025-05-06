import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../services/api'

export const useJobResultsStore = defineStore('job_results', () => {
  const results = ref([])
  const isLoading = ref(false)
  const error = ref(null)
  const filters = ref({ search: '' })
  const pagination = ref({
    currentPage: 1,
    itemsPerPage: 5,
    totalItems: 0,
    totalPages: 0,
  })

  async function fetchResults(page = 1, newFilters = null) {
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
      if (params.search) {
        params.search = params.search
      }
      Object.keys(params).forEach(key => (params[key] == null || params[key] === '') && delete params[key])
      const response = await api.get('/job-results/', { params })
      console.log('job-results API response items:', response.data.items)
      if (response.data && Array.isArray(response.data.items)) {
        results.value = response.data.items
        pagination.value.totalItems = response.data.total
        pagination.value.totalPages = response.data.pages
        pagination.value.currentPage = response.data.page
        pagination.value.itemsPerPage = response.data.size
      } else {
        results.value = []
        resetPagination()
        error.value = 'Received invalid data format from server.'
      }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch job results'
      results.value = []
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
    results.value = []
    isLoading.value = false
    error.value = null
    filters.value = { search: '' }
    resetPagination()
    pagination.value.itemsPerPage = 5
  }

  // Summary metrics for dashboard cards
  const summary = computed(() => {
    const total = results.value.length
    const running = results.value.filter(r => r.status === 'running').length
    const succeeded = results.value.filter(r => r.status === 'completed' || r.status === 'success').length
    const failed = results.value.filter(r => r.status === 'failed' || r.status === 'error').length
    return { total, running, succeeded, failed }
  })

  return {
    results, isLoading, error, filters, pagination, summary, fetchResults, $reset
  }
}) 