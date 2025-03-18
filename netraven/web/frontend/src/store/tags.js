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
      
      console.log(`=== STORE DEBUG: fetchTagsForDevice ===`)
      console.log(`Method called with deviceId:`, deviceId)
      console.log(`deviceId type:`, typeof deviceId)
      
      try {
        console.log(`Fetching tags for device ${deviceId}`)
        
        // Instead of checking each tag for the device,
        // use the device/{deviceId}/tags endpoint directly
        const deviceTags = await tagService.getTagsForDevice(deviceId)
        console.log(`Got tags for device ${deviceId}:`, deviceTags)
        
        // Update our local cache
        this.deviceTags[deviceId] = deviceTags
        console.log(`Updated deviceTags in store:`, this.deviceTags)
        console.log(`=== END STORE DEBUG ===`)
        
        return deviceTags
      } catch (error) {
        this.error = error.response?.data?.detail || `Failed to fetch tags for device ${deviceId}`
        console.error(`Error fetching tags for device ${deviceId}:`, error)
        console.error('Error details:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status
        })
        
        // If API call fails, use cached data if available
        if (this.deviceTags[deviceId] && this.deviceTags[deviceId].length > 0) {
          console.log(`Using cached tags for device ${deviceId}`)
          return this.deviceTags[deviceId]
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
        console.log(`Assigning tag ${tagId} to device ${deviceId}`)
        
        // Add more detailed logging
        console.log('API call parameters:', {
          deviceIds: [deviceId],
          tagIds: [tagId]
        })
        
        // Call the API to assign the tag to the device
        const result = await tagService.assignTagsToDevices([deviceId], [tagId])
        
        console.log('API response:', result)
        
        if (!result) {
          throw new Error(`Failed to assign tag ${tagId} to device ${deviceId}: No response from API`)
        }
        
        if (!result.success) {
          console.error('Assignment failed with result:', result)
          throw new Error(result.message || `Failed to assign tag ${tagId} to device ${deviceId}`)
        }
        
        console.log('Tag assignment successful, refreshing device tags')
        
        // Refresh the device tags from the server to ensure we have the latest data
        await this.fetchTagsForDevice(deviceId)
        
        // Return the updated tags
        return this.deviceTags[deviceId] || []
      } catch (error) {
        const errorMessage = error.response?.data?.detail || error.message || `Failed to assign tag ${tagId} to device ${deviceId}`
        this.error = errorMessage
        console.error(`Error assigning tag ${tagId} to device ${deviceId}:`, error)
        console.error('Error details:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status
        })
        throw error
      } finally {
        this.loading = false
      }
    },
    
    // Remove a tag from a device
    async removeTagFromDevice(deviceId, tagId) {
      this.loading = true
      this.error = null
      
      try {
        console.log(`Removing tag ${tagId} from device ${deviceId}`)
        
        // Add more detailed logging
        console.log('API call parameters:', {
          deviceIds: [deviceId],
          tagIds: [tagId]
        })
        
        // Call the API to remove the tag from the device
        const result = await tagService.removeTagsFromDevices([deviceId], [tagId])
        
        console.log('API response:', result)
        
        if (!result) {
          throw new Error(`Failed to remove tag ${tagId} from device ${deviceId}: No response from API`)
        }
        
        if (!result.success) {
          console.error('Removal failed with result:', result)
          throw new Error(result.message || `Failed to remove tag ${tagId} from device ${deviceId}`)
        }
        
        console.log('Tag removal successful, refreshing device tags')
        
        // Refresh the device tags from the server to ensure we have the latest data
        await this.fetchTagsForDevice(deviceId)
        
        // Return the updated tags
        return this.deviceTags[deviceId] || []
      } catch (error) {
        const errorMessage = error.response?.data?.detail || error.message || `Failed to remove tag ${tagId} from device ${deviceId}`
        this.error = errorMessage
        console.error(`Error removing tag ${tagId} from device ${deviceId}:`, error)
        console.error('Error details:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status
        })
        throw error
      } finally {
        this.loading = false
      }
    }
  }
}) 