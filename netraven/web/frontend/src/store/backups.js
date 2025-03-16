import { defineStore } from 'pinia'
import { backupService } from '../api/api'

export const useBackupStore = defineStore('backups', {
  state: () => ({
    backups: [],
    currentBackup: null,
    currentBackupContent: null,
    loading: false,
    error: null
  }),
  
  getters: {
    getBackupById: (state) => (id) => {
      return state.backups.find(backup => backup.id === id)
    },
    
    backupsByDevice: (state) => (deviceId) => {
      return state.backups.filter(backup => backup.device_id === deviceId)
    }
  },
  
  actions: {
    async fetchBackups(params = {}) {
      this.loading = true
      this.error = null
      
      try {
        const backups = await backupService.getBackups(params)
        this.backups = backups
        console.log('Backup Store: Successfully loaded backup data')
        return backups
      } catch (error) {
        console.error('Backup Store: Error fetching backups:', error)
        this.error = error.response?.data?.detail || 'Failed to fetch backups'
        this.backups = []
        return []
      } finally {
        this.loading = false
      }
    },
    
    async fetchBackup(id) {
      this.loading = true
      this.error = null
      
      try {
        const backup = await backupService.getBackup(id)
        this.currentBackup = backup
        
        // Update the backup in the backups array if it exists
        const index = this.backups.findIndex(backup => backup.id === id)
        if (index !== -1) {
          this.backups[index] = backup
        }
        
        return backup
      } catch (error) {
        console.error(`Backup Store: Error fetching backup ${id}:`, error)
        this.error = error.response?.data?.detail || `Failed to fetch backup ${id}`
        return null
      } finally {
        this.loading = false
      }
    },
    
    async fetchBackupContent(id) {
      this.loading = true
      this.error = null
      
      try {
        const content = await backupService.getBackupContent(id)
        this.currentBackupContent = content
        return content
      } catch (error) {
        console.error(`Backup Store: Error fetching backup content for ${id}:`, error)
        this.error = error.response?.data?.detail || `Failed to fetch backup content for ${id}`
        return null
      } finally {
        this.loading = false
      }
    },
    
    async compareBackups(backup1Id, backup2Id) {
      this.loading = true
      this.error = null
      
      try {
        const comparison = await backupService.compareBackups(backup1Id, backup2Id)
        return comparison
      } catch (error) {
        console.error(`Backup Store: Error comparing backups ${backup1Id} and ${backup2Id}:`, error)
        this.error = error.response?.data?.detail || `Failed to compare backups ${backup1Id} and ${backup2Id}`
        return null
      } finally {
        this.loading = false
      }
    },
    
    async restoreBackup(id) {
      this.loading = true
      this.error = null
      
      try {
        const result = await backupService.restoreBackup(id)
        return result
      } catch (error) {
        console.error(`Backup Store: Error restoring backup ${id}:`, error)
        this.error = error.response?.data?.detail || `Failed to restore backup ${id}`
        return null
      } finally {
        this.loading = false
      }
    },
    
    async deleteBackup(id) {
      this.loading = true
      this.error = null
      
      try {
        await backupService.deleteBackup(id)
        
        // Remove the backup from the backups array
        this.backups = this.backups.filter(backup => backup.id !== id)
        
        // Clear currentBackup if it matches the deleted backup
        if (this.currentBackup && this.currentBackup.id === id) {
          this.currentBackup = null
          this.currentBackupContent = null
        }
        
        return true
      } catch (error) {
        console.error(`Backup Store: Error deleting backup ${id}:`, error)
        this.error = error.response?.data?.detail || `Failed to delete backup ${id}`
        return false
      } finally {
        this.loading = false
      }
    }
  }
}) 