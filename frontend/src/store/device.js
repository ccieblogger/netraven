import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'
import { getLatestReachabilityJobResult } from '../services/api'

export const useDeviceStore = defineStore('devices', () => {
  const devices = ref([])
  const isLoading = ref(false)
  const error = ref(null)
  const deviceCredentials = ref([])
  const isLoadingCredentials = ref(false)
  const credentialError = ref(null)
  const deviceCredentialsCache = ref({})

  async function fetchDevices(params = {}) {
    isLoading.value = true
    error.value = null
    try {
      const response = await api.get('/devices/', { params })
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

  async function fetchDeviceCredentials(deviceId) {
    isLoadingCredentials.value = true
    credentialError.value = null
    
    if (deviceCredentialsCache.value[deviceId]) {
      isLoadingCredentials.value = false
      return deviceCredentialsCache.value[deviceId]
    }
    try {
      const response = await api.get(`/devices/${deviceId}/credentials`)
      const deduped = Array.isArray(response.data)
        ? response.data.filter((cred, idx, arr) => arr.findIndex(c => c.id === cred.id) === idx)
        : []
      deviceCredentials.value = deduped
      deviceCredentialsCache.value[deviceId] = deduped
      return deduped
    } catch (err) {
      credentialError.value = err.response?.data?.detail || 'Failed to fetch device credentials'
      console.error("Fetch Device Credentials Error:", err)
      return []
    } finally {
      isLoadingCredentials.value = false
    }
  }

  async function createDevice(deviceData) {
    isLoading.value = true
    error.value = null
    try {
      // Prepare API data - standardize field names between frontend and backend
      const apiData = {
        ...deviceData,
        // Convert tag_ids from the form to tags expected by the API
        tags: deviceData.tag_ids || []
      }
      delete apiData.tag_ids
      const response = await api.post('/devices/', apiData);
      devices.value.push(response.data)
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to create device.'
      return false
    } finally {
      isLoading.value = false
    }
  }

  async function updateDevice(deviceId, deviceData) {
    isLoading.value = true
    error.value = null
    try {
      const apiData = {
        ...deviceData,
        tags: deviceData.tag_ids || []
      }
      delete apiData.tag_ids
      const response = await api.put(`/devices/${deviceId}`, apiData);
      const index = devices.value.findIndex(d => d.id === deviceId)
      if (index !== -1) {
        devices.value[index] = response.data
      }
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to update device.'
      return false
    } finally {
      isLoading.value = false
    }
  }

  async function deleteDevice(deviceId) {
    isLoading.value = true
    error.value = null
    try {
      await api.delete(`/devices/${deviceId}`);
      devices.value = devices.value.filter(d => d.id !== deviceId)
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to delete device.'
      return false
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch devices and their latest reachability job result
   */
  async function fetchDevicesWithReachabilityStatus(params = {}) {
    await fetchDevices(params);
    // For each device, fetch the latest reachability job result
    await Promise.all(devices.value.map(async (device) => {
      const result = await getLatestReachabilityJobResult(device.id);
      device.last_reachability_status = result ? result.status : null;
    }));
  }

  function $reset() {
    devices.value = []
    isLoading.value = false
    error.value = null
    deviceCredentials.value = []
    isLoadingCredentials.value = false
    credentialError.value = null
    deviceCredentialsCache.value = {}
  }

  return { 
    devices, 
    isLoading, 
    error, 
    deviceCredentials,
    isLoadingCredentials,
    credentialError,
    fetchDevices, 
    createDevice, 
    updateDevice, 
    deleteDevice, 
    fetchDeviceCredentials,
    $reset,
    deviceCredentialsCache,
    fetchDevicesWithReachabilityStatus
  }
})