import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export const useDeviceStore = defineStore('devices', () => {
  const devices = ref([])
  const isLoading = ref(false)
  const error = ref(null)

  async function fetchDevices() {
    isLoading.value = true
    error.value = null
    try {
      const response = await api.get('/devices')
      devices.value = response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch devices'
      console.error("Fetch Devices Error:", err)
    } finally {
      isLoading.value = false
    }
  }

  async function createDevice(deviceData) {
     isLoading.value = true
     error.value = null
     try {
       const response = await api.post('/devices', deviceData)
       devices.value.push(response.data) 
       return true
     } catch (err) {
       error.value = err.response?.data?.detail || 'Failed to create device'
       console.error("Create Device Error:", err)
       return false
     } finally {
       isLoading.value = false
     }
  }

  async function updateDevice(deviceId, deviceData) {
    isLoading.value = true
    error.value = null
    try {
      const response = await api.put(`/devices/${deviceId}`, deviceData)
      const index = devices.value.findIndex(d => d.id === deviceId)
      if (index !== -1) {
        devices.value[index] = response.data
      }
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to update device'
      console.error("Update Device Error:", err)
      return false
    } finally {
      isLoading.value = false
    }
  }

  async function deleteDevice(deviceId) {
    isLoading.value = true
    error.value = null
    try {
      await api.delete(`/devices/${deviceId}`)
      devices.value = devices.value.filter(d => d.id !== deviceId)
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to delete device'
      console.error("Delete Device Error:", err)
      return false
    } finally {
      isLoading.value = false
    }
  }

  function $reset() {
    devices.value = []
    isLoading.value = false
    error.value = null
  }

  return { devices, isLoading, error, fetchDevices, createDevice, updateDevice, deleteDevice, $reset }
}) 