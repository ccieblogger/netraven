import { defineStore } from 'pinia'
import { apiClient } from '../api/api'
import { useNotificationStore } from './notification'

export const useKeyStore = defineStore('key', {
  state: () => ({
    keys: [],
    activeKey: null,
    loading: false,
    error: null,
    rotationResult: null,
    backupResult: null,
    restoreResult: null
  }),
  
  getters: {
    sortedKeys: (state) => {
      return [...state.keys].sort((a, b) => {
        if (a.active && !b.active) return -1
        if (!a.active && b.active) return 1
        return new Date(b.created_at) - new Date(a.created_at)
      })
    },
    
    hasActiveKey: (state) => {
      return !!state.activeKey
    },
    
    hasKeys: (state) => {
      return state.keys.length > 0
    }
  },
  
  actions: {
    async fetchKeys() {
      this.loading = true
      this.error = null
      
      try {
        const response = await apiClient.getKeys()
        this.keys = response.data.keys || []
        this.activeKey = this.keys.find(key => key.active) || null
        return response.data
      } catch (error) {
        this.keys = response.keys
        this.activeKeyId = response.active_key_id
        return response
      } catch (error) {
        console.error('Error fetching keys:', error)
        this.error = error.message || 'Failed to fetch keys'
        return { keys: [], active_key_id: null }
      } finally {
        this.loading = false
      }
    },
    
    async fetchKey(id) {
      this.loading = true
      this.error = null
      
      try {
        const data = await apiClient.getKey(id)
        this.key = data
        return data
      } catch (error) {
        console.error(`Error fetching key ${id}:`, error)
        this.error = error.message || 'Failed to fetch key'
        return null
      } finally {
        this.loading = false
      }
    },
    
    async createKey(description = null) {
      this.loading = true
      this.error = null
      
      try {
        const data = await apiClient.createKey({ description })
        await this.fetchKeys() // Refresh the list
        return data
      } catch (error) {
        console.error('Error creating key:', error)
        this.error = error.message || 'Failed to create key'
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async activateKey(keyId) {
      this.loading = true
      this.error = null
      
      try {
        const data = await apiClient.activateKey({ key_id: keyId })
        await this.fetchKeys() // Refresh the list
        return data
      } catch (error) {
        console.error(`Error activating key ${keyId}:`, error)
        this.error = error.message || 'Failed to activate key'
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async rotateKeys(force = false, description = null) {
      this.loading = true
      this.error = null
      
      try {
        const data = await apiClient.rotateKeys({ force, description })
        this.rotationResult = data
        await this.fetchKeys() // Refresh the list
        return data
      } catch (error) {
        console.error('Error rotating keys:', error)
        this.error = error.message || 'Failed to rotate keys'
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async createBackup(password, keyIds = null) {
      this.loading = true
      this.error = null
      
      try {
        const data = await apiClient.createKeyBackup({ password, key_ids: keyIds })
        this.backupResult = data
        return data
      } catch (error) {
        console.error('Error creating key backup:', error)
        this.error = error.message || 'Failed to create key backup'
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async restoreKeys(backupData, password, activateKey = false) {
      this.loading = true
      this.error = null
      
      try {
        const data = await apiClient.restoreKeys({ 
          backup_data: backupData, 
          password, 
          activate_key: activateKey 
        })
        this.restoreResult = data
        await this.fetchKeys() // Refresh the list
        return data
      } catch (error) {
        console.error('Error restoring keys:', error)
        this.error = error.message || 'Failed to restore keys'
        throw error
      } finally {
        this.loading = false
      }
    }
  }
}) 