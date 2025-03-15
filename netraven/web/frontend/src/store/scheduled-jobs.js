import { defineStore } from 'pinia'
import { scheduledJobsService } from '../api/api'

export const useScheduledJobStore = defineStore('scheduledJobs', {
  state: () => ({
    scheduledJobs: [],
    currentScheduledJob: null,
    loading: false,
    error: null,
    filters: {
      job_type: null,
      enabled: null,
      device_id: null
    }
  }),
  
  getters: {
    getScheduledJobById: (state) => (id) => {
      return state.scheduledJobs.find(job => job.id === id)
    },
    
    enabledJobs: (state) => {
      return state.scheduledJobs.filter(job => job.enabled)
    }
  },
  
  actions: {
    async fetchScheduledJobs(params = {}) {
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
        
        const scheduledJobs = await scheduledJobsService.getScheduledJobs(queryParams)
        this.scheduledJobs = scheduledJobs
        return scheduledJobs
      } catch (error) {
        console.error('Scheduled Job Store: Error fetching scheduled jobs:', error)
        this.error = error.response?.data?.detail || 'Failed to fetch scheduled jobs'
        return []
      } finally {
        this.loading = false
      }
    },
    
    async fetchScheduledJob(id) {
      this.loading = true
      this.error = null
      
      try {
        const scheduledJob = await scheduledJobsService.getScheduledJob(id)
        this.currentScheduledJob = scheduledJob
        
        // Update the scheduled job in the scheduled jobs array if it exists
        const index = this.scheduledJobs.findIndex(job => job.id === id)
        if (index !== -1) {
          this.scheduledJobs[index] = scheduledJob
        }
        
        return scheduledJob
      } catch (error) {
        console.error(`Scheduled Job Store: Error fetching scheduled job ${id}:`, error)
        this.error = error.response?.data?.detail || `Failed to fetch scheduled job ${id}`
        return null
      } finally {
        this.loading = false
      }
    },
    
    async createScheduledJob(jobData) {
      this.loading = true
      this.error = null
      
      try {
        const newJob = await scheduledJobsService.createScheduledJob(jobData)
        this.scheduledJobs.push(newJob)
        return newJob
      } catch (error) {
        console.error('Scheduled Job Store: Error creating scheduled job:', error)
        this.error = error.response?.data?.detail || 'Failed to create scheduled job'
        return null
      } finally {
        this.loading = false
      }
    },
    
    async updateScheduledJob(id, jobData) {
      this.loading = true
      this.error = null
      
      try {
        const updatedJob = await scheduledJobsService.updateScheduledJob(id, jobData)
        
        // Update the scheduled job in the scheduled jobs array
        const index = this.scheduledJobs.findIndex(job => job.id === id)
        if (index !== -1) {
          this.scheduledJobs[index] = updatedJob
        }
        
        // Update currentScheduledJob if it matches the updated job
        if (this.currentScheduledJob && this.currentScheduledJob.id === id) {
          this.currentScheduledJob = updatedJob
        }
        
        return updatedJob
      } catch (error) {
        console.error(`Scheduled Job Store: Error updating scheduled job ${id}:`, error)
        this.error = error.response?.data?.detail || `Failed to update scheduled job ${id}`
        return null
      } finally {
        this.loading = false
      }
    },
    
    async deleteScheduledJob(id) {
      this.loading = true
      this.error = null
      
      try {
        await scheduledJobsService.deleteScheduledJob(id)
        
        // Remove the scheduled job from the scheduled jobs array
        this.scheduledJobs = this.scheduledJobs.filter(job => job.id !== id)
        
        // Clear currentScheduledJob if it matches the deleted job
        if (this.currentScheduledJob && this.currentScheduledJob.id === id) {
          this.currentScheduledJob = null
        }
        
        return true
      } catch (error) {
        console.error(`Scheduled Job Store: Error deleting scheduled job ${id}:`, error)
        this.error = error.response?.data?.detail || `Failed to delete scheduled job ${id}`
        return false
      } finally {
        this.loading = false
      }
    },
    
    async runScheduledJob(id) {
      this.loading = true
      this.error = null
      
      try {
        const result = await scheduledJobsService.runScheduledJob(id)
        return result
      } catch (error) {
        console.error(`Scheduled Job Store: Error running scheduled job ${id}:`, error)
        this.error = error.response?.data?.detail || `Failed to run scheduled job ${id}`
        return null
      } finally {
        this.loading = false
      }
    },
    
    async toggleScheduledJob(id, enabled) {
      this.loading = true
      this.error = null
      
      try {
        const result = await scheduledJobsService.toggleScheduledJob(id, enabled)
        
        // Update the scheduled job in the scheduled jobs array
        const index = this.scheduledJobs.findIndex(job => job.id === id)
        if (index !== -1) {
          this.scheduledJobs[index].enabled = enabled
        }
        
        // Update currentScheduledJob if it matches the toggled job
        if (this.currentScheduledJob && this.currentScheduledJob.id === id) {
          this.currentScheduledJob.enabled = enabled
        }
        
        return result
      } catch (error) {
        console.error(`Scheduled Job Store: Error toggling scheduled job ${id}:`, error)
        this.error = error.response?.data?.detail || `Failed to toggle scheduled job ${id}`
        return null
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
        enabled: null,
        device_id: null
      }
    }
  }
}) 