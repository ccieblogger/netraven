import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export const useCredentialStore = defineStore('credential', () => {
  const credentials = ref([])
  const isLoading = ref(false)
  const error = ref(null)

  async function fetchCredentials() {
    isLoading.value = true
    error.value = null
    try {
      const response = await api.get('/credentials/')
      if (response.data && response.data.items) {
        credentials.value = response.data.items
      } else if (Array.isArray(response.data)) {
        credentials.value = response.data
      } else {
        credentials.value = []
      }
    } catch (err) {
      console.error("Error fetching credentials:", err)
      error.value = err.response?.data?.detail || 'Failed to fetch credentials'
      credentials.value = []
    } finally {
      isLoading.value = false
    }
  }

  async function createCredential(credentialData) {
     isLoading.value = true
     error.value = null
     try {
       const response = await api.post('/credentials/', credentialData)
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
      const response = await api.put(`/credentials/${credentialId}/`, credentialData)
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
    isLoading.value = true;
    error.value = null;
    
    // Get the credential to check if it's a system credential
    const credential = credentials.value.find(c => c.id === credentialId);
    if (credential && credential.is_system) {
      error.value = 'System credentials cannot be deleted';
      isLoading.value = false;
      return false;
    }
    
    try {
      await api.delete(`/credentials/${credentialId}/`);
      credentials.value = credentials.value.filter(c => c.id !== credentialId);
      return true;
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to delete credential';
      console.error("Delete Credential Error:", err);
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  function $reset() {
    credentials.value = []
    isLoading.value = false
    error.value = null
  }

  return {
    credentials,
    isLoading,
    error,
    fetchCredentials,
    createCredential,
    updateCredential,
    deleteCredential,
    $reset
  }
})

 