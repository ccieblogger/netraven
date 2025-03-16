import { defineStore } from 'pinia'
import { deviceService } from '../api/api'

export const useDeviceStore = defineStore('devices', {
  state: () => ({
    devices: [],
    currentDevice: null,
    loading: false,
    error: null
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
    async fetchDevices() {
      this.loading = true
      this.error = null
      
      try {
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
        console.error('Device Store: Error fetching devices:', error)
        this.error = error.response?.data?.detail || 'Failed to fetch devices'
        this.devices = []
        return []
      } finally {
        this.loading = false
      }
    },
    
    async fetchDevice(id) {
      this.loading = true
      this.error = null
      
      try {
        const device = await deviceService.getDevice(id)
        this.currentDevice = device
        
        // Update the device in the devices array if it exists
        const index = this.devices.findIndex(d => d.id === id)
        if (index !== -1) {
          this.devices[index] = device
        }
        
        return device
      } catch (error) {
        console.error(`Device Store: Error fetching device ${id}:`, error)
        this.error = error.response?.data?.detail || `Failed to fetch device ${id}`
        return null
      } finally {
        this.loading = false
      }
    },
    
    async createDevice(deviceData) {
      this.loading = true
      this.error = null
      
      try {
        console.log('Creating device with data:', deviceData)
        const newDevice = await deviceService.createDevice(deviceData)
        console.log('Device created:', newDevice)
        this.devices.push(newDevice)
        return newDevice
      } catch (error) {
        console.error('Error creating device:', error)
        console.error('Error response:', error.response?.data)
        this.error = error.response?.data?.detail || 'Failed to create device'
        return null
      } finally {
        this.loading = false
      }
    },
    
    async updateDevice(id, deviceData) {
      this.loading = true
      this.error = null
      
      try {
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
        console.error(`Device Store: Error updating device ${id}:`, error)
        this.error = error.response?.data?.detail || `Failed to update device ${id}`
        return null
      } finally {
        this.loading = false
      }
    },
    
    async deleteDevice(id) {
      this.loading = true
      this.error = null
      
      try {
        await deviceService.deleteDevice(id)
        
        // Remove the device from the devices array
        this.devices = this.devices.filter(device => device.id !== id)
        
        // Clear currentDevice if it matches the deleted device
        if (this.currentDevice && this.currentDevice.id === id) {
          this.currentDevice = null
        }
        
        return true
      } catch (error) {
        console.error(`Device Store: Error deleting device ${id}:`, error)
        this.error = error.response?.data?.detail || `Failed to delete device ${id}`
        return false
      } finally {
        this.loading = false
      }
    },
    
    async backupDevice(id) {
      this.loading = true
      this.error = null
      
      try {
        const result = await deviceService.backupDevice(id)
        return result
      } catch (error) {
        console.error(`Device Store: Error backing up device ${id}:`, error)
        this.error = error.response?.data?.detail || `Failed to backup device ${id}`
        return null
      } finally {
        this.loading = false
      }
    },
    
    async checkDeviceReachability(id) {
      this.loading = true
      this.error = null
      
      try {
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
        console.error(`Device Store: Error checking device reachability ${id}:`, error)
        this.error = error.response?.data?.detail || `Failed to check device reachability ${id}`
        return null
      } finally {
        this.loading = false
      }
    }
  }
}) 