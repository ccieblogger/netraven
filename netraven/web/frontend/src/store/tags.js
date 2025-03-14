import { defineStore } from 'pinia'
import { tagService } from '../api/api'

// Create a single default tag
const DEFAULT_TAGS = [
  {
    id: 'tag-default',
    name: 'Default',
    color: '#6366F1', // Indigo color
    description: 'Default tag for all devices',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }
];

export const useTagStore = defineStore('tags', {
  state: () => ({
    tags: [...DEFAULT_TAGS], // Initialize with just the default tag
    currentTag: null,
    deviceTags: {},  // Map of device ID -> tags for that device
    loading: false,
    error: null
  }),
  
  getters: {
    getTagById: (state) => (id) => {
      return state.tags.find(tag => tag.id === id)
    },
    
    getTagByName: (state) => (name) => {
      return state.tags.find(tag => tag.name === name)
    },
    
    getTagsForDevice: (state) => (deviceId) => {
      return state.deviceTags[deviceId] || []
    }
  },
  
  actions: {
    async fetchTags() {
      this.loading = true
      this.error = null
      
      try {
        // Call the API to get all tags
        console.log('Fetching all tags')
        const tags = await tagService.getTags()
        
        // Update the store with the tags from the API
        this.tags = tags
        
        // Ensure we have at least the default tag if the API returns no tags
        if (this.tags.length === 0) {
          this.tags = [...DEFAULT_TAGS]
        }
        
        return this.tags
      } catch (error) {
        this.error = error.message || 'Failed to fetch tags'
        console.error('Error fetching tags:', error)
        return []
      } finally {
        this.loading = false
      }
    },
    
    async fetchTag(id) {
      this.loading = true
      this.error = null
      
      try {
        console.log(`Fetching tag with ID: ${id}`)
        const tag = await tagService.getTag(id)
        this.currentTag = tag
        
        // Update the tag in the tags array if it exists
        const index = this.tags.findIndex(t => t.id === id)
        if (index !== -1) {
          this.tags[index] = tag
        } else {
          this.tags.push(tag)
        }
        
        return tag
      } catch (error) {
        // Check if it's a 404 not found error
        if (error.response && error.response.status === 404) {
          console.error(`Tag with ID ${id} was not found in the database`)
          this.error = `Tag with ID ${id} not found`
        } else {
          this.error = error.response?.data?.detail || `Failed to fetch tag ${id}`
          console.error(`Error fetching tag ${id}:`, error)
        }
        return null
      } finally {
        this.loading = false
      }
    },
    
    async fetchDevicesForTag(id) {
      this.loading = true
      this.error = null
      
      try {
        const devices = await tagService.getDevicesForTag(id)
        return devices
      } catch (error) {
        this.error = error.response?.data?.detail || `Failed to fetch devices for tag ${id}`
        console.error(`Error fetching devices for tag ${id}:`, error)
        return []
      } finally {
        this.loading = false
      }
    },
    
    async fetchTagsForDevice(deviceId) {
      this.loading = true
      this.error = null
      
      try {
        console.log(`Fetching tags for device ${deviceId}`)
        
        // Make sure we have all available tags loaded first
        if (this.tags.length === 0) {
          await this.fetchTags()
        }
        
        // Get the device-specific tags from the API
        const deviceTags = await tagService.getDevicesForTag(deviceId)
        
        // Update our local cache
        this.deviceTags[deviceId] = deviceTags
        
        return deviceTags
      } catch (error) {
        this.error = error.response?.data?.detail || `Failed to fetch tags for device ${deviceId}`
        console.error(`Error fetching tags for device ${deviceId}:`, error)
        
        // If API call fails, use cached data if available
        if (this.deviceTags[deviceId] && this.deviceTags[deviceId].length > 0) {
          console.log(`Using cached tags for device ${deviceId}`)
          return this.deviceTags[deviceId]
        }
        
        // If no cache, use default tag
        if (this.tags.length > 0) {
          const defaultTag = this.tags[0]
          this.deviceTags[deviceId] = [defaultTag]
          console.log(`Assigned default tag ${defaultTag.id} to device ${deviceId}`)
          return [defaultTag]
        }
        
        return []
      } finally {
        this.loading = false
      }
    },
    
    async createTag(tagData) {
      this.loading = true
      this.error = null
      
      try {
        console.log('Creating new tag with data:', tagData)
        
        // Call the API to create the tag
        const newTag = await tagService.createTag(tagData)
        
        // Add the server-created tag to our local state
        this.tags.push(newTag)
        
        console.log('Created new tag:', newTag)
        return newTag
      } catch (error) {
        this.error = error.response?.data?.detail || error.message || 'Failed to create tag'
        console.error('Error creating tag:', error)
        return null
      } finally {
        this.loading = false
      }
    },
    
    async updateTag(id, tagData) {
      this.loading = true
      this.error = null
      
      try {
        console.log(`Updating tag ${id} with data:`, tagData)
        
        // Call the API to update the tag
        const updatedTag = await tagService.updateTag(id, tagData)
        
        // Update the tag in the tags array
        const index = this.tags.findIndex(t => t.id === id)
        if (index !== -1) {
          this.tags[index] = updatedTag
        }
        
        // Update currentTag if it matches
        if (this.currentTag && this.currentTag.id === id) {
          this.currentTag = updatedTag
        }
        
        return updatedTag
      } catch (error) {
        // Check if it's a 404 not found error
        if (error.response && error.response.status === 404) {
          console.error(`Tag with ID ${id} was not found in the database`)
          this.error = `Tag with ID ${id} not found`
        } else {
          this.error = error.response?.data?.detail || `Failed to update tag ${id}`
          console.error(`Error updating tag ${id}:`, error)
        }
        return null
      } finally {
        this.loading = false
      }
    },
    
    async deleteTag(id) {
      this.loading = true
      this.error = null
      
      try {
        // Call the API to delete the tag
        await tagService.deleteTag(id)
        
        // Remove the tag from the tags array
        this.tags = this.tags.filter(t => t.id !== id)
        
        // Clear currentTag if it matches
        if (this.currentTag && this.currentTag.id === id) {
          this.currentTag = null
        }
        
        // Remove from deviceTags
        for (const deviceId in this.deviceTags) {
          this.deviceTags[deviceId] = this.deviceTags[deviceId].filter(t => t.id !== id)
        }
        
        console.log(`Successfully deleted tag ${id}`)
        return true
      } catch (error) {
        // Check if it's a 404 not found error
        if (error.response && error.response.status === 404) {
          console.error(`Tag with ID ${id} was not found in the database`)
          
          // Still remove from local state if it doesn't exist on the server
          this.tags = this.tags.filter(t => t.id !== id)
          
          if (this.currentTag && this.currentTag.id === id) {
            this.currentTag = null
          }
          
          // Return success since we've removed it locally
          return true
        }
        
        this.error = error.response?.data?.detail || `Failed to delete tag ${id}`
        console.error(`Error deleting tag ${id}:`, error)
        return false
      } finally {
        this.loading = false
      }
    },
    
    async assignTagsToDevices(deviceIds, tagIds) {
      this.loading = true
      this.error = null
      
      try {
        const result = await tagService.assignTagsToDevices(deviceIds, tagIds)
        
        // Update deviceTags cache for each device
        for (const deviceId of deviceIds) {
          // Remove existing cache for this device to force refresh
          delete this.deviceTags[deviceId]
        }
        
        return result
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to assign tags to devices'
        console.error('Error assigning tags to devices:', error)
        return null
      } finally {
        this.loading = false
      }
    },
    
    async removeTagsFromDevices(deviceIds, tagIds) {
      this.loading = true
      this.error = null
      
      try {
        const result = await tagService.removeTagsFromDevices(deviceIds, tagIds)
        
        // Update deviceTags cache for each device
        for (const deviceId of deviceIds) {
          // Remove existing cache for this device to force refresh
          delete this.deviceTags[deviceId]
        }
        
        return result
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to remove tags from devices'
        console.error('Error removing tags from devices:', error)
        return null
      } finally {
        this.loading = false
      }
    },
    
    // Add single tag to a single device
    async assignTagToDevice(deviceId, tagId) {
      this.loading = true
      this.error = null
      
      try {
        // In a real app, this would make an API call to update the backend
        // For our mock implementation, we'll just update the store
        
        // Get current device tags or initialize empty array
        const currentTags = this.deviceTags[deviceId] || []
        
        // Find the tag object from available tags
        const tagToAdd = this.tags.find(tag => tag.id === tagId)
        
        if (!tagToAdd) {
          throw new Error(`Tag with ID ${tagId} not found`)
        }
        
        // Check if tag is already assigned
        if (currentTags.some(tag => tag.id === tagId)) {
          console.log(`Tag ${tagId} already assigned to device ${deviceId}`)
          return currentTags
        }
        
        // Add the tag to the device
        const updatedTags = [...currentTags, tagToAdd]
        
        // Update the store
        this.deviceTags[deviceId] = updatedTags
        
        console.log(`Assigned tag ${tagId} to device ${deviceId}`)
        return updatedTags
      } catch (error) {
        this.error = error.message || `Failed to assign tag ${tagId} to device ${deviceId}`
        console.error(this.error, error)
        throw error
      } finally {
        this.loading = false
      }
    },
    
    // Remove single tag from a single device
    async removeTagFromDevice(deviceId, tagId) {
      this.loading = true
      this.error = null
      
      try {
        // In a real app, this would make an API call to update the backend
        // For our mock implementation, we'll just update the store
        
        // Get current device tags or initialize empty array
        const currentTags = this.deviceTags[deviceId] || []
        
        // Remove the tag from the device
        const updatedTags = currentTags.filter(tag => tag.id !== tagId)
        
        // Update the store
        this.deviceTags[deviceId] = updatedTags
        
        console.log(`Removed tag ${tagId} from device ${deviceId}`)
        return updatedTags
      } catch (error) {
        this.error = error.message || `Failed to remove tag ${tagId} from device ${deviceId}`
        console.error(this.error, error)
        throw error
      } finally {
        this.loading = false
      }
    }
  }
}) 