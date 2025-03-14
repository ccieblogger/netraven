import { defineStore } from 'pinia'
import { backupService } from '../api/api'

// Mock data for development and error recovery
const mockBackups = [
  {
    id: 'backup-1',
    device_id: 'device-1',
    filename: 'router-01_20230401_config.txt',
    size: 12580,
    status: 'completed',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    id: 'backup-2',
    device_id: 'device-2',
    filename: 'switch-01_20230402_config.txt',
    size: 8720,
    status: 'completed',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    id: 'backup-3',
    device_id: 'device-3',
    filename: 'firewall-01_20230403_config.txt',
    size: 15640,
    status: 'completed',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }
];

export const useBackupStore = defineStore('backups', {
  state: () => ({
    backups: [],
    currentBackup: null,
    currentBackupContent: null,
    loading: false,
    error: null,
    useMockData: false
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
        // First attempt to get real data
        const backups = await backupService.getBackups(params)
        this.backups = backups
        this.useMockData = false
        console.log('Backup Store: Successfully loaded real backup data')
        return backups
      } catch (error) {
        console.error('Backup Store: Error fetching backups, using mock data:', error)
        this.error = error.response?.data?.detail || 'Failed to fetch backups'
        
        // If real data fails, use mock data as a fallback
        this.backups = [...mockBackups]
        this.useMockData = true
        console.log('Backup Store: Using mock backup data')
        return this.backups
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
        const index = this.backups.findIndex(b => b.id === id)
        if (index !== -1) {
          this.backups[index] = backup
        } else {
          this.backups.push(backup)
        }
        
        return backup
      } catch (error) {
        this.error = error.response?.data?.detail || `Failed to fetch backup ${id}`
        console.error(`Error fetching backup ${id}:`, error)
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
        this.error = error.response?.data?.detail || `Failed to fetch backup content for ${id}`
        console.error(`Error fetching backup content for ${id}:`, error)
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
        this.error = error.response?.data?.detail || 'Failed to compare backups'
        console.error('Error comparing backups:', error)
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
        this.error = error.response?.data?.detail || `Failed to restore backup ${id}`
        console.error(`Error restoring backup ${id}:`, error)
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
        this.backups = this.backups.filter(b => b.id !== id)
        
        // Clear currentBackup if it matches the deleted backup
        if (this.currentBackup && this.currentBackup.id === id) {
          this.currentBackup = null
          this.currentBackupContent = null
        }
        
        return true
      } catch (error) {
        this.error = error.response?.data?.detail || `Failed to delete backup ${id}`
        console.error(`Error deleting backup ${id}:`, error)
        return false
      } finally {
        this.loading = false
      }
    }
  }
}) 