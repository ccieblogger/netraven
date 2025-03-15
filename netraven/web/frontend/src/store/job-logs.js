import { defineStore } from 'pinia'
import { jobLogsService } from '../api/api'

export const useJobLogStore = defineStore('jobLogs', {
  state: () => ({
    jobLogs: [],
    currentJobLog: null,
    currentJobLogEntries: [],
    loading: false,
    error: null,
    filters: {
      job_type: null,
      status: null,
      device_id: null,
      start_date: null,
      end_date: null
    }
  }),
  
  getters: {
    getJobLogById: (state) => (id) => {
      return state.jobLogs.find(log => log.id === id)
    }
  },
  
  actions: {
    async fetchJobLogs(params = {}) {
      this.loading = true
      this.error = null
      
      try {
        // Merge filters with any additional params
        const queryParams = { ...this.filters, ...params }
        
        // Remove null or undefined values
        Object.keys(queryParams).forEach(key => {
          if (queryParams[key] === null || queryParams[key] === undefined) {
            delete queryParams[key]
          }
        })
        
        const jobLogs = await jobLogsService.getJobLogs(queryParams)
        this.jobLogs = jobLogs
        return jobLogs
      } catch (error) {
        console.error('Job Log Store: Error fetching job logs:', error)
        this.error = error.response?.data?.detail || 'Failed to fetch job logs'
        return []
      } finally {
        this.loading = false
      }
    },
    
    async fetchJobLog(id, includeEntries = false) {
      this.loading = true
      this.error = null
      
      try {
        const jobLog = await jobLogsService.getJobLog(id, includeEntries)
        this.currentJobLog = jobLog
        
        // Update the job log in the job logs array if it exists
        const index = this.jobLogs.findIndex(log => log.id === id)
        if (index !== -1) {
          this.jobLogs[index] = jobLog
        }
        
        return jobLog
      } catch (error) {
        console.error(`Job Log Store: Error fetching job log ${id}:`, error)
        this.error = error.response?.data?.detail || `Failed to fetch job log ${id}`
        return null
      } finally {
        this.loading = false
      }
    },
    
    async fetchJobLogEntries(id, params = {}) {
      this.loading = true
      this.error = null
      
      try {
        const entries = await jobLogsService.getJobLogEntries(id, params)
        this.currentJobLogEntries = entries
        return entries
      } catch (error) {
        console.error(`Job Log Store: Error fetching job log entries for ${id}:`, error)
        this.error = error.response?.data?.detail || `Failed to fetch job log entries for ${id}`
        return []
      } finally {
        this.loading = false
      }
    },
    
    async deleteJobLog(id) {
      this.loading = true
      this.error = null
      
      try {
        await jobLogsService.deleteJobLog(id)
        
        // Remove the job log from the job logs array
        this.jobLogs = this.jobLogs.filter(log => log.id !== id)
        
        // Clear currentJobLog if it matches the deleted job log
        if (this.currentJobLog && this.currentJobLog.id === id) {
          this.currentJobLog = null
          this.currentJobLogEntries = []
        }
        
        return true
      } catch (error) {
        console.error(`Job Log Store: Error deleting job log ${id}:`, error)
        this.error = error.response?.data?.detail || `Failed to delete job log ${id}`
        return false
      } finally {
        this.loading = false
      }
    },
    
    setFilters(filters) {
      this.filters = { ...this.filters, ...filters }
    },
    
    clearFilters() {
      this.filters = {
        job_type: null,
        status: null,
        device_id: null,
        start_date: null,
        end_date: null
      }
    }
  }
}) 