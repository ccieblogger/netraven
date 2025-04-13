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
      const response = await api.get('/devices/')
      if (response.data && response.data.items) {
        devices.value = response.data.items
      } else {
        devices.value = Array.isArray(response.data) ? response.data : []
      }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch devices'
      console.error("Fetch Devices Error:", err)
      devices.value = []
    } finally {
      isLoading.value = false
    }
  }

  async function createDevice(deviceData) {
    isLoading.value = true
    error.value = null
    try {
      // TEMPORARY: Handle credential_id until proper tag-based credential matching is implemented
      // TODO: Replace with tag-based credential matching in future implementation
      const apiData = {
        ...deviceData,
        // Rename tag_ids to tags as expected by API
        tags: deviceData.tag_ids || [],
        // Include credential_id if present (temporary implementation)
        credential_id: deviceData.credential_id
      }
      
      // Remove properties not needed by API
      delete apiData.tag_ids
      
      const response = await api.post('/devices/', apiData)
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
      // TEMPORARY: Handle credential_id until proper tag-based credential matching is implemented
      // TODO: Replace with tag-based credential matching in future implementation
      const apiData = {
        ...deviceData,
        // Rename tag_ids to tags as expected by API
        tags: deviceData.tag_ids || [],
        // Include credential_id if present (temporary implementation)
        credential_id: deviceData.credential_id
      }
      
      // Remove properties not needed by API
      delete apiData.tag_ids
      
      const response = await api.put(`/devices/${deviceId}/`, apiData)
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
      await api.delete(`/devices/${deviceId}/`)
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