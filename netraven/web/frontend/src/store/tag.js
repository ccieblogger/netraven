import { defineStore } from 'pinia'
import { apiClient } from '../api/api'

export const useTagStore = defineStore('tag', {
  state: () => ({
    tags: [],
    loading: false,
    error: null
  }),

  getters: {
    getTagById: (state) => (id) => {
      return state.tags.find(tag => tag.id === id)
    }
  },

  actions: {
    async fetchTags() {
      this.loading = true
      this.error = null
      
      try {
        const data = await apiClient.getTags()
        this.tags = data
      } catch (error) {
        console.error('Error loading tags:', error)
        this.error = error.message || 'Failed to load tags'
      } finally {
        this.loading = false
      }
    },
    
    async createTag(tagData) {
      this.loading = true
      this.error = null
      
      try {
        const createdTag = await apiClient.createTag(tagData)
        this.tags.push(createdTag)
        return createdTag
      } catch (error) {
        console.error('Error creating tag:', error)
        this.error = error.message || 'Failed to create tag'
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async updateTag(tagId, tagData) {
      this.loading = true
      this.error = null
      
      try {
        const updatedTag = await apiClient.updateTag(tagId, tagData)
        const index = this.tags.findIndex(tag => tag.id === tagId)
        
        if (index !== -1) {
          this.tags[index] = updatedTag
        }
        
        return updatedTag
      } catch (error) {
        console.error('Error updating tag:', error)
        this.error = error.message || 'Failed to update tag'
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async deleteTag(tagId) {
      this.loading = true
      this.error = null
      
      try {
        await apiClient.deleteTag(tagId)
        this.tags = this.tags.filter(tag => tag.id !== tagId)
      } catch (error) {
        console.error('Error deleting tag:', error)
        this.error = error.message || 'Failed to delete tag'
        throw error
      } finally {
        this.loading = false
      }
    }
  }
}) 