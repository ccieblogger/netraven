import { defineStore } from 'pinia'
import { tagRuleService } from '../api/api'

export const useTagRuleStore = defineStore('tagRules', {
  state: () => ({
    tagRules: [],
    currentTagRule: null,
    testResults: null,
    loading: false,
    error: null
  }),
  
  getters: {
    getTagRuleById: (state) => (id) => {
      return state.tagRules.find(rule => rule.id === id)
    },
    
    activeTagRules: (state) => {
      return state.tagRules.filter(rule => rule.is_active)
    }
  },
  
  actions: {
    async fetchTagRules() {
      this.loading = true
      this.error = null
      
      try {
        const rules = await tagRuleService.getTagRules()
        this.tagRules = rules
        return rules
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to fetch tag rules'
        console.error('Error fetching tag rules:', error)
        return []
      } finally {
        this.loading = false
      }
    },
    
    async fetchTagRule(id) {
      this.loading = true
      this.error = null
      
      try {
        const rule = await tagRuleService.getTagRule(id)
        this.currentTagRule = rule
        
        // Update the rule in the rules array if it exists
        const index = this.tagRules.findIndex(r => r.id === id)
        if (index !== -1) {
          this.tagRules[index] = rule
        } else {
          this.tagRules.push(rule)
        }
        
        return rule
      } catch (error) {
        this.error = error.response?.data?.detail || `Failed to fetch tag rule ${id}`
        console.error(`Error fetching tag rule ${id}:`, error)
        return null
      } finally {
        this.loading = false
      }
    },
    
    async createTagRule(ruleData) {
      this.loading = true
      this.error = null
      
      try {
        const newRule = await tagRuleService.createTagRule(ruleData)
        this.tagRules.push(newRule)
        return newRule
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to create tag rule'
        console.error('Error creating tag rule:', error)
        return null
      } finally {
        this.loading = false
      }
    },
    
    async updateTagRule(id, ruleData) {
      this.loading = true
      this.error = null
      
      try {
        const updatedRule = await tagRuleService.updateTagRule(id, ruleData)
        
        // Update the rule in the rules array
        const index = this.tagRules.findIndex(r => r.id === id)
        if (index !== -1) {
          this.tagRules[index] = updatedRule
        }
        
        // Update currentTagRule if it matches
        if (this.currentTagRule && this.currentTagRule.id === id) {
          this.currentTagRule = updatedRule
        }
        
        return updatedRule
      } catch (error) {
        this.error = error.response?.data?.detail || `Failed to update tag rule ${id}`
        console.error(`Error updating tag rule ${id}:`, error)
        return null
      } finally {
        this.loading = false
      }
    },
    
    async deleteTagRule(id) {
      this.loading = true
      this.error = null
      
      try {
        await tagRuleService.deleteTagRule(id)
        
        // Remove the rule from the rules array
        this.tagRules = this.tagRules.filter(r => r.id !== id)
        
        // Clear currentTagRule if it matches
        if (this.currentTagRule && this.currentTagRule.id === id) {
          this.currentTagRule = null
        }
        
        return true
      } catch (error) {
        this.error = error.response?.data?.detail || `Failed to delete tag rule ${id}`
        console.error(`Error deleting tag rule ${id}:`, error)
        return false
      } finally {
        this.loading = false
      }
    },
    
    async applyTagRule(id) {
      this.loading = true
      this.error = null
      
      try {
        const result = await tagRuleService.applyTagRule(id)
        return result
      } catch (error) {
        this.error = error.response?.data?.detail || `Failed to apply tag rule ${id}`
        console.error(`Error applying tag rule ${id}:`, error)
        return null
      } finally {
        this.loading = false
      }
    },
    
    async testRule(ruleCriteria) {
      this.loading = true
      this.error = null
      this.testResults = null
      
      try {
        const results = await tagRuleService.testRule(ruleCriteria)
        this.testResults = results
        return results
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to test rule criteria'
        console.error('Error testing rule criteria:', error)
        return null
      } finally {
        this.loading = false
      }
    }
  }
}) 