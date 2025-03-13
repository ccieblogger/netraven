import { defineStore } from 'pinia'
import { tagService } from '../api/api'

export const useTagStore = defineStore('tags', {
  state: () => ({
    tags: [],
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
        const tags = await tagService.getTags()
        this.tags = tags
        return tags
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to fetch tags'
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
        this.error = error.response?.data?.detail || `Failed to fetch tag ${id}`
        console.error(`Error fetching tag ${id}:`, error)
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
        // Assuming we fetch all tags and filter them
        // In a real app, you might want a dedicated API endpoint
        if (!this.tags.length) {
          await this.fetchTags()
        }
        
        // For now, we're just stubbing this - in a real implementation
        // this would query the API for tags related to this device
        const deviceTagIds = []
        const deviceTags = this.tags.filter(tag => deviceTagIds.includes(tag.id))
        
        // Store in device tags map
        this.deviceTags[deviceId] = deviceTags
        
        return deviceTags
      } catch (error) {
        this.error = error.response?.data?.detail || `Failed to fetch tags for device ${deviceId}`
        console.error(`Error fetching tags for device ${deviceId}:`, error)
        return []
      } finally {
        this.loading = false
      }
    },
    
    async createTag(tagData) {
      this.loading = true
      this.error = null
      
      try {
        const newTag = await tagService.createTag(tagData)
        this.tags.push(newTag)
        return newTag
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to create tag'
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
        this.error = error.response?.data?.detail || `Failed to update tag ${id}`
        console.error(`Error updating tag ${id}:`, error)
        return null
      } finally {
        this.loading = false
      }
    },
    
    async deleteTag(id) {
      this.loading = true
      this.error = null
      
      try {
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
        
        return true
      } catch (error) {
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
    }
  }
}) 