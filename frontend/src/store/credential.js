import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export const useCredentialStore = defineStore('credentials', () => {
  const credentials = ref([])
  const isLoading = ref(false)
  const error = ref(null)

  async function fetchCredentials() {
    isLoading.value = true
    error.value = null
    try {
      const response = await api.get('/credentials')
      credentials.value = response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch credentials'
      console.error("Fetch Credentials Error:", err)
    } finally {
      isLoading.value = false
    }
  }

  async function createCredential(credentialData) {
     isLoading.value = true
     error.value = null
     try {
       const response = await api.post('/credentials', credentialData)
       credentials.value.push(response.data) 
       return true
     } catch (err) {
       error.value = err.response?.data?.detail || 'Failed to create credential'
       console.error("Create Credential Error:", err)
       return false
     } finally {
       isLoading.value = false
     }
  }

  async function updateCredential(credentialId, credentialData) {
    isLoading.value = true
    error.value = null
    try {
      const response = await api.put(`/credentials/${credentialId}`, credentialData)
      const index = credentials.value.findIndex(c => c.id === credentialId)
      if (index !== -1) {
        credentials.value[index] = response.data
      }
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to update credential'
      console.error("Update Credential Error:", err)
      return false
    } finally {
      isLoading.value = false
    }
  }

  async function deleteCredential(credentialId) {
    isLoading.value = true
    error.value = null
    try {
      await api.delete(`/credentials/${credentialId}`)
      credentials.value = credentials.value.filter(c => c.id !== credentialId)
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to delete credential'
      console.error("Delete Credential Error:", err)
      return false
    } finally {
      isLoading.value = false
    }
  }

  function $reset() {
    credentials.value = []
    isLoading.value = false
    error.value = null
  }

 