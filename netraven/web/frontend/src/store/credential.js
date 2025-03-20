import { defineStore } from 'pinia'
import { apiClient } from '../api/api'

export const useCredentialStore = defineStore('credential', {
  state: () => ({
    credentials: [],
    credential: null,
    loading: false,
    error: null,
    filters: {},
    testResults: null,
    tagAssociations: {},
    dashboardStats: null
  }),
  
  getters: {
    getCredentialById: (state) => (id) => {
      return state.credentials.find(c => c.id === id) || null
    },
    
    credentialsByTag: (state) => (tagId) => {
      return state.credentials.filter(c => 
        c.tags && c.tags.some(tag => tag.id === tagId)
      )
    },
    
    getMostSuccessfulCredentials: (state) => {
      return [...state.credentials]
        .sort((a, b) => {
          const aSuccessRate = a.success_count / (a.success_count + a.failure_count || 1)
          const bSuccessRate = b.success_count / (b.success_count + b.failure_count || 1)
          return bSuccessRate - aSuccessRate
        })
        .slice(0, 5)
    },
    
    getLeastSuccessfulCredentials: (state) => {
      return [...state.credentials]
        .filter(c => c.success_count + c.failure_count > 0) // Only include used credentials
        .sort((a, b) => {
          const aSuccessRate = a.success_count / (a.success_count + a.failure_count || 1)
          const bSuccessRate = b.success_count / (b.success_count + b.failure_count || 1)
          return aSuccessRate - bSuccessRate
        })
        .slice(0, 5)
    }
  },
  
  actions: {
    async fetchCredentials(params = {}) {
      this.loading = true
      this.error = null
      
      try {
        const data = await apiClient.getCredentials(params)
        this.credentials = data
        return data
      } catch (error) {
        console.error('Error fetching credentials:', error)
        this.error = error.message || 'Failed to fetch credentials'
        return []
      } finally {
        this.loading = false
      }
    },
    
    async fetchCredential(id, includeTags = true) {
      this.loading = true
      this.error = null
      
      try {
        const data = await apiClient.getCredential(id, includeTags)
        this.credential = data
        return data
      } catch (error) {
        console.error(`Error fetching credential ${id}:`, error)
        this.error = error.message || 'Failed to fetch credential'
        return null
      } finally {
        this.loading = false
      }
    },
    
    async createCredential(credential) {
      this.loading = true
      this.error = null
      
      try {
        const data = await apiClient.createCredential(credential)
        await this.fetchCredentials() // Refresh the list
        return data
      } catch (error) {
        console.error('Error creating credential:', error)
        this.error = error.message || 'Failed to create credential'
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async updateCredential(id, credential) {
      this.loading = true
      this.error = null
      
      try {
        const data = await apiClient.updateCredential(id, credential)
        
        // Update the credential in the list
        const index = this.credentials.findIndex(c => c.id === id)
        if (index !== -1) {
          this.credentials[index] = data
        }
        
        return data
      } catch (error) {
        console.error(`Error updating credential ${id}:`, error)
        this.error = error.message || 'Failed to update credential'
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async deleteCredential(id) {
      this.loading = true
      this.error = null
      
      try {
        await apiClient.deleteCredential(id)
        
        // Remove the credential from the list
        this.credentials = this.credentials.filter(c => c.id !== id)
        
        return true
      } catch (error) {
        console.error(`Error deleting credential ${id}:`, error)
        this.error = error.message || 'Failed to delete credential'
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async fetchCredentialsByTag(tagId) {
      this.loading = true
      this.error = null
      
      try {
        const data = await apiClient.getCredentialsByTag(tagId)
        this.tagAssociations[tagId] = data
        return data
      } catch (error) {
        console.error(`Error fetching credentials for tag ${tagId}:`, error)
        this.error = error.message || 'Failed to fetch credentials by tag'
        return []
      } finally {
        this.loading = false
      }
    },
    
    async associateCredentialWithTag(credentialId, tagId, priority = 0) {
      this.loading = true
      this.error = null
      
      try {
        const data = await apiClient.associateCredentialWithTag({
          credentialId,
          tagId,
          priority
        })
        
        // Refresh the credential to update its tags
        await this.fetchCredential(credentialId)
        
        return data
      } catch (error) {
        console.error('Error associating credential with tag:', error)
        this.error = error.message || 'Failed to associate credential with tag'
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async removeCredentialFromTag(credentialId, tagId) {
      this.loading = true
      this.error = null
      
      try {
        await apiClient.removeCredentialFromTag(credentialId, tagId)
        
        // Refresh the credential to update its tags
        await this.fetchCredential(credentialId)
        
        return true
      } catch (error) {
        console.error('Error removing credential from tag:', error)
        this.error = error.message || 'Failed to remove credential from tag'
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async testCredential(credentialId, testParams) {
      this.loading = true
      this.error = null
      this.testResults = null
      
      try {
        const data = await apiClient.testCredential(credentialId, testParams)
        this.testResults = data
        return data
      } catch (error) {
        console.error(`Error testing credential ${credentialId}:`, error)
        this.error = error.message || 'Failed to test credential'
        this.testResults = { success: false, error: error.message }
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async fetchDashboardStats() {
      this.loading = true
      this.error = null
      
      try {
        // First get all credentials
        await this.fetchCredentials()
        
        // Calculate some stats
        const totalCredentials = this.credentials.length
        const totalSuccess = this.credentials.reduce((sum, c) => sum + c.success_count, 0)
        const totalFailure = this.credentials.reduce((sum, c) => sum + c.failure_count, 0)
        
        const successRate = totalSuccess + totalFailure > 0 
          ? (totalSuccess / (totalSuccess + totalFailure) * 100).toFixed(1) 
          : 0
          
        // Group by device type (based on tags)
        const deviceTypes = {}
        this.credentials.forEach(credential => {
          if (credential.tags) {
            credential.tags.forEach(tag => {
              if (!deviceTypes[tag.name]) {
                deviceTypes[tag.name] = {
                  count: 0,
                  success: 0,
                  failure: 0
                }
              }
              
              deviceTypes[tag.name].count++
              deviceTypes[tag.name].success += tag.success_count || 0
              deviceTypes[tag.name].failure += tag.failure_count || 0
            })
          }
        })
        
        this.dashboardStats = {
          totalCredentials,
          totalSuccess,
          totalFailure,
          successRate,
          deviceTypes,
          mostSuccessful: this.getMostSuccessfulCredentials,
          leastSuccessful: this.getLeastSuccessfulCredentials
        }
        
        return this.dashboardStats
      } catch (error) {
        console.error('Error fetching dashboard stats:', error)
        this.error = error.message || 'Failed to fetch dashboard stats'
        return null
      } finally {
        this.loading = false
      }
    }
  }
}) 