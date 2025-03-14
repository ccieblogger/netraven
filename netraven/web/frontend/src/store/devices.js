import { defineStore } from 'pinia'
import { deviceService } from '../api/api'

// Mock data for development and error recovery
const mockDevices = [
  {
    id: 'device-1',
    hostname: 'router-01',
    ip_address: '192.168.1.1',
    device_type: 'router',
    vendor: 'Cisco',
    model: 'ISR 4321',
    status: 'online',
    enabled: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    id: 'device-2',
    hostname: 'switch-01',
    ip_address: '192.168.1.2',
    device_type: 'switch',
    vendor: 'Cisco',
    model: 'Catalyst 3850',
    status: 'online',
    enabled: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    id: 'device-3',
    hostname: 'firewall-01',
    ip_address: '192.168.1.3',
    device_type: 'firewall',
    vendor: 'Fortinet',
    model: 'FortiGate 100E',
    status: 'offline',
    enabled: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }
];

export const useDeviceStore = defineStore('devices', {
  state: () => ({
    devices: [],
    currentDevice: null,
    loading: false,
    error: null,
    useMockData: false
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
        // First attempt to get real data
        const devices = await deviceService.getDevices()
        this.devices = devices
        this.useMockData = false
        console.log('Device Store: Successfully loaded real device data')
        return devices
      } catch (error) {
        console.error('Device Store: Error fetching devices, using mock data:', error)
        this.error = error.response?.data?.detail || 'Failed to fetch devices'
        
        // If real data fails, use mock data as a fallback
        this.devices = [...mockDevices]
        this.useMockData = true
        console.log('Device Store: Using mock device data')
        return this.devices
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
        } else {
          this.devices.push(device)
        }
        
        return device
      } catch (error) {
        this.error = error.response?.data?.detail || `Failed to fetch device ${id}`
        console.error(`Error fetching device ${id}:`, error)
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
        const index = this.devices.findIndex(d => d.id === id)
        if (index !== -1) {
          this.devices[index] = updatedDevice
        }
        
        // Update currentDevice if it matches the updated device
        if (this.currentDevice && this.currentDevice.id === id) {
          this.currentDevice = updatedDevice
        }
        
        return updatedDevice
      } catch (error) {
        this.error = error.response?.data?.detail || `Failed to update device ${id}`
        console.error(`Error updating device ${id}:`, error)
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
        this.devices = this.devices.filter(d => d.id !== id)
        
        // Clear currentDevice if it matches the deleted device
        if (this.currentDevice && this.currentDevice.id === id) {
          this.currentDevice = null
        }
        
        return true
      } catch (error) {
        this.error = error.response?.data?.detail || `Failed to delete device ${id}`
        console.error(`Error deleting device ${id}:`, error)
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
        this.error = error.response?.data?.detail || `Failed to backup device ${id}`
        console.error(`Error backing up device ${id}:`, error)
        return null
      } finally {
        this.loading = false
      }
    }
  }
}) 