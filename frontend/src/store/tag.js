import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api' // Import the configured Axios instance
// import { useNotificationStore } from './notifications' // Optional for user feedback

export const useTagStore = defineStore('tag', () => {
  // const notifications = useNotificationStore()
  const tags = ref([])
  const isLoading = ref(false)
  const error = ref(null)

  async function fetchTags() {
    isLoading.value = true
    error.value = null
    try {
      const response = await api.get('/tags/')
      // Handle pagination response structure
      if (response.data && response.data.items) {
        // API returns paginated response with items array
        tags.value = response.data.items;
      } else if (Array.isArray(response.data)) {
        // Fallback for array response
        tags.value = response.data;
      } else {
        // Default to empty array if response format is unexpected
        tags.value = [];
      }
    } catch (err) {
      console.error("Error fetching tags:", err)
      error.value = err.response?.data?.detail || 'Failed to fetch tags'
      tags.value = [] // Clear tags on error
    } finally {
      isLoading.value = false
    }
  }

  async function createTag(tagData) {
     isLoading.value = true
     error.value = null
     try {
       const response = await api.post('/tags/', tagData)
       tags.value.push(response.data) // Add to local state
       // notifications.addMessage({ type: 'success', text: 'Tag created successfully' })
       return true // Indicate success
     } catch (err) {
       error.value = err.response?.data?.detail || 'Failed to create tag'
       console.error("Create Tag Error:", err)
       // notifications.addMessage({ type: 'error', text: error.value })
       return false // Indicate failure
     } finally {
       isLoading.value = false
     }
  }

  async function updateTag(tagId, tagData) {
    isLoading.value = true
    error.value = null
    try {
      // Use relative URL without trailing slash to match backend
      const response = await api.put(`/tags/${tagId}`, tagData)
      // Update local state
      const index = tags.value.findIndex(t => t.id === tagId)
      if (index !== -1) {
        tags.value[index] = response.data
      }
      // notifications.addMessage({ type: 'success', text: 'Tag updated successfully' })
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to update tag'
      console.error("Update Tag Error:", err)
      // notifications.addMessage({ type: 'error', text: error.value })
      return false
    } finally {
      isLoading.value = false
    }
  }

  async function deleteTag(tagId) {
    isLoading.value = true
    error.value = null
    try {
      await api.delete(`/tags/${tagId}/`)
      // Remove from local state
      tags.value = tags.value.filter(t => t.id !== tagId)
      // notifications.addMessage({ type: 'success', text: 'Tag deleted successfully' })
      return true
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to delete tag'
      console.error("Delete Tag Error:", err)
      // notifications.addMessage({ type: 'error', text: error.value })
      return false
    } finally {
      isLoading.value = false
    }
  }

  // Reset function might be useful
  function $reset() {
    tags.value = []
    isLoading.value = false
    error.value = null
  }

  return { tags, isLoading, error, fetchTags, createTag, updateTag, deleteTag, $reset }
}) 