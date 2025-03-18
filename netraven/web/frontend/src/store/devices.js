import { defineStore } from 'pinia'
import { deviceService } from '../api/api'
import { useAuthStore } from './auth'

export const useDeviceStore = defineStore('devices', {
  state: () => ({
    devices: [],
    currentDevice: null,
    loading: false,
    error: null,
    authError: false
  }),
  
  getters: {
    getDeviceById: (state) => (id) => {
      return state.devices.find(device => device.id === id)
    },
    
    enabledDevices: (state) => {
      return state.devices.filter(device => device.enabled)
    }
  },
  
  actions: {
    // Reset error state
    resetError() {
      this.error = null
      this.authError = false
    },
    
    // Handle API errors with special handling for auth errors
    handleApiError(error, operation) {
      console.error(`Device Store: Error during ${operation}:`, error)
      
      // Check for authentication errors
      if (error.isAuthError || error.response?.status === 401) {
        console.error(`Authentication error during ${operation}`)
        this.authError = true
        this.error = 'Authentication error: Please log in again'
        
        // Notify auth store of the issue
        const authStore = useAuthStore()
        authStore.clearAuth()
      } else if (error.response?.data?.detail) {
        // Use backend error message if available
        this.error = error.response.data.detail
      } else {
        // Generic error message
        this.error = `Failed to ${operation}`
      }
    },
    
    async fetchDevices() {
      this.loading = true
      this.resetError()
      
      try {
        // Verify authentication and permissions first
        const authStore = useAuthStore()
        if (!authStore.validateToken()) {
          this.authError = true
          this.error = 'Authentication required'
          this.devices = []
          return []
        }
        
        const devices = await deviceService.getDevices()
        
        // Ensure each device has a tags array
        devices.forEach(device => {
          if (!device.tags) {
            device.tags = []
          }
        })
        
        this.devices = devices
        console.log('Device Store: Successfully loaded device data')
        return devices
      } catch (error) {
        this.handleApiError(error, 'fetch devices')
        this.devices = []
        return []
      } finally {
        this.loading = false
      }
    },
    
    async fetchDevice(id) {
      this.loading = true
      this.resetError()
      
      try {
        // Verify authentication first
        const authStore = useAuthStore()
        if (!authStore.validateToken()) {
          this.authError = true
          this.error = 'Authentication required'
          return null
        }
        
        const device = await deviceService.getDevice(id)
        this.currentDevice = device
        
        // Update the device in the devices array if it exists
        const index = this.devices.findIndex(d => d.id === id)
        if (index !== -1) {
          this.devices[index] = device
        }
        
        return device
      } catch (error) {
        this.handleApiError(error, `fetch device ${id}`)
        return null
      } finally {
        this.loading = false
      }
    },
    
    async createDevice(deviceData) {
      this.loading = true
      this.resetError()
      
      try {
        console.log('Creating device with data:', deviceData)
        
        // Verify authentication and permissions first
        const authStore = useAuthStore()
        if (!authStore.validateToken()) {
          this.authError = true
          this.error = 'Authentication required'
          return null
        }
        
        // Verify device management permissions
        if (!authStore.verifyDeviceManagementPermission()) {
          this.error = 'You do not have permission to create devices'
          return null
        }
        
        const newDevice = await deviceService.createDevice(deviceData)
        console.log('Device created:', newDevice)
        this.devices.push(newDevice)
        return newDevice
      } catch (error) {
        this.handleApiError(error, 'create device')
        return null
      } finally {
        this.loading = false
      }
    },
    
    async updateDevice(id, deviceData) {
      this.loading = true
      this.resetError()
      
      try {
        // Verify authentication first
        const authStore = useAuthStore()
        if (!authStore.validateToken()) {
          this.authError = true
          this.error = 'Authentication required'
          return null
        }
        
        const updatedDevice = await deviceService.updateDevice(id, deviceData)
        
        // Update the device in the devices array
        const index = this.devices.findIndex(device => device.id === id)
        if (index !== -1) {
          this.devices[index] = updatedDevice
        }
        
        // Update currentDevice if it matches the updated device
        if (this.currentDevice && this.currentDevice.id === id) {
          this.currentDevice = updatedDevice
        }
        
        return updatedDevice
      } catch (error) {
        this.handleApiError(error, `update device ${id}`)
        return null
      } finally {
        this.loading = false
      }
    },
    
    async deleteDevice(id) {
      this.loading = true
      this.resetError()
      
      try {
        // Verify authentication first
        const authStore = useAuthStore()
        if (!authStore.validateToken()) {
          this.authError = true
          this.error = 'Authentication required'
          return false
        }
        
        await deviceService.deleteDevice(id)
        
        // Remove the device from the devices array
        this.devices = this.devices.filter(device => device.id !== id)
        
        // Clear currentDevice if it matches the deleted device
        if (this.currentDevice && this.currentDevice.id === id) {
          this.currentDevice = null
        }
        
        return true
      } catch (error) {
        this.handleApiError(error, `delete device ${id}`)
        return false
      } finally {
        this.loading = false
      }
    },
    
    async backupDevice(id) {
      this.loading = true
      this.resetError()
      
      try {
        // Verify authentication first
        const authStore = useAuthStore()
        if (!authStore.validateToken()) {
          this.authError = true
          this.error = 'Authentication required'
          return null
        }
        
        console.log(`DeviceStore: Initiating backup for device ${id}`)
        const result = await deviceService.backupDevice(id)
        console.log(`DeviceStore: Backup initiated successfully for device ${id}`, result)
        return result
      } catch (error) {
        console.error(`DeviceStore: Error during backup for device ${id}:`, error)
        console.error(`DeviceStore: Error response:`, error.response?.data)
        this.handleApiError(error, `backup device ${id}`)
        return null
      } finally {
        this.loading = false
      }
    },
    
    async checkDeviceReachability(id) {
      this.loading = true
      this.resetError()
      
      try {
        // Verify authentication first
        const authStore = useAuthStore()
        if (!authStore.validateToken()) {
          this.authError = true
          this.error = 'Authentication required'
          return null
        }
        
        const result = await deviceService.checkDeviceReachability(id)
        
        // Update the device in the devices array
        const index = this.devices.findIndex(device => device.id === id)
        if (index !== -1 && result.status) {
          this.devices[index].status = result.status
        }
        
        // Update currentDevice if it matches the checked device
        if (this.currentDevice && this.currentDevice.id === id && result.status) {
          this.currentDevice.status = result.status
        }
        
        return result
      } catch (error) {
        this.handleApiError(error, `check device reachability ${id}`)
        return null
      } finally {
        this.loading = false
      }
    }
  }
}) 