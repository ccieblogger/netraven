<template>
  <MainLayout>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">Tag Rules</h1>
      <button 
        @click="showCreateModal = true" 
        class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
      >
        Add New Rule
      </button>
    </div>
    
    <div v-if="loading" class="text-center py-8">
      <p>Loading tag rules...</p>
    </div>
    
    <div v-else-if="rules.length === 0" class="bg-white rounded-lg shadow p-6 text-center">
      <p class="text-gray-600 mb-4">No tag rules have been created yet.</p>
      <button 
        @click="showCreateModal = true" 
        class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
      >
        Create Your First Rule
      </button>
    </div>
    
    <div v-else class="bg-white rounded-lg shadow overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Rule Name
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Tag
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Created
            </th>
            <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="rule in rules" :key="rule.id">
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="text-sm font-medium text-gray-900">
                {{ rule.name }}
              </div>
              <div class="text-sm text-gray-500">
                {{ rule.description || 'No description' }}
              </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <TagBadge 
                v-if="rule.tag_name" 
                :tag="{ name: rule.tag_name, color: rule.tag_color }" 
              />
              <span v-else class="text-sm text-gray-500">No tag</span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span 
                class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full"
                :class="rule.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'"
              >
                {{ rule.is_active ? 'Active' : 'Inactive' }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="text-sm text-gray-500">
                {{ formatDate(rule.created_at) }}
              </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
              <button
                @click="applyRule(rule)"
                class="text-green-600 hover:text-green-900 mr-2"
                :disabled="!rule.is_active"
                :class="{'opacity-50 cursor-not-allowed': !rule.is_active}"
                title="Apply this rule to all devices"
              >
                Apply
              </button>
              <button
                @click="editRule(rule)"
                class="text-blue-600 hover:text-blue-900 mr-2"
              >
                Edit
              </button>
              <button
                @click="confirmDelete(rule)"
                class="text-red-600 hover:text-red-900"
              >
                Delete
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- Create Rule Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-lg p-6 w-full max-w-3xl overflow-y-auto max-h-[90vh]">
        <h2 class="text-xl font-bold mb-4">Add New Tag Rule</h2>
        
        <div class="mb-4">
          <label class="block text-gray-700 text-sm font-bold mb-2" for="name">
            Rule Name
          </label>
          <input
            id="name"
            v-model="newRule.name"
            type="text"
            class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            placeholder="Enter rule name"
          />
        </div>
        
        <div class="mb-4">
          <label class="block text-gray-700 text-sm font-bold mb-2" for="description">
            Description
          </label>
          <textarea
            id="description"
            v-model="newRule.description"
            class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            placeholder="Enter rule description"
            rows="2"
          ></textarea>
        </div>
        
        <div class="mb-4">
          <label class="block text-gray-700 text-sm font-bold mb-2" for="tag_id">
            Tag to Apply
          </label>
          <select
            id="tag_id"
            v-model="newRule.tag_id"
            class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
          >
            <option value="" disabled selected>Select a tag</option>
            <option v-for="tag in tags" :key="tag.id" :value="tag.id">
              {{ tag.name }}
            </option>
          </select>
        </div>
        
        <div class="mb-4">
          <label class="block text-gray-700 text-sm font-bold mb-2">
            Rule Criteria
          </label>
          <div class="p-4 border rounded bg-gray-50">
            <div v-if="Object.keys(ruleBuilder).length === 0" class="text-center py-4">
              <button 
                @click="addSimpleCondition" 
                class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm mr-2"
              >
                Add Condition
              </button>
              <button 
                @click="addComplexOperator" 
                class="bg-purple-500 hover:bg-purple-600 text-white px-3 py-1 rounded text-sm"
              >
                Add Group
              </button>
            </div>
            
            <div v-else>
              <div v-if="ruleBuilder.field">
                <!-- Simple condition -->
                <div class="flex flex-wrap items-center gap-2">
                  <select 
                    v-model="ruleBuilder.field" 
                    class="border rounded px-2 py-1 text-sm"
                  >
                    <option value="hostname">Hostname</option>
                    <option value="ip_address">IP Address</option>
                    <option value="device_type">Device Type</option>
                    <option value="description">Description</option>
                  </select>
                  
                  <select 
                    v-model="ruleBuilder.operator" 
                    class="border rounded px-2 py-1 text-sm"
                  >
                    <option value="equals">equals</option>
                    <option value="contains">contains</option>
                    <option value="startswith">starts with</option>
                    <option value="endswith">ends with</option>
                    <option value="regex">matches regex</option>
                  </select>
                  
                  <input 
                    v-model="ruleBuilder.value" 
                    type="text" 
                    class="border rounded px-2 py-1 text-sm flex-grow"
                    placeholder="Value"
                  />
                  
                  <button 
                    @click="clearRuleBuilder" 
                    class="bg-red-500 hover:bg-red-600 text-white px-2 py-1 rounded text-sm"
                  >
                    Remove
                  </button>
                </div>
              </div>
              
              <div v-else-if="ruleBuilder.type">
                <!-- Complex operator (AND/OR) -->
                <div class="border-l-2 border-blue-400 pl-3 py-2">
                  <div class="flex items-center mb-2">
                    <select 
                      v-model="ruleBuilder.type" 
                      class="border rounded px-2 py-1 text-sm font-bold bg-blue-50"
                    >
                      <option value="and">AND (All conditions must match)</option>
                      <option value="or">OR (Any condition can match)</option>
                    </select>
                    
                    <button 
                      @click="clearRuleBuilder" 
                      class="ml-2 bg-red-500 hover:bg-red-600 text-white px-2 py-1 rounded text-sm"
                    >
                      Remove Group
                    </button>
                  </div>
                  
                  <div v-for="(condition, index) in ruleBuilder.conditions" :key="index" class="mb-2">
                    <div v-if="condition.field" class="flex flex-wrap items-center gap-2 mb-1">
                      <select 
                        v-model="condition.field" 
                        class="border rounded px-2 py-1 text-sm"
                      >
                        <option value="hostname">Hostname</option>
                        <option value="ip_address">IP Address</option>
                        <option value="device_type">Device Type</option>
                        <option value="description">Description</option>
                      </select>
                      
                      <select 
                        v-model="condition.operator" 
                        class="border rounded px-2 py-1 text-sm"
                      >
                        <option value="equals">equals</option>
                        <option value="contains">contains</option>
                        <option value="startswith">starts with</option>
                        <option value="endswith">ends with</option>
                        <option value="regex">matches regex</option>
                      </select>
                      
                      <input 
                        v-model="condition.value" 
                        type="text" 
                        class="border rounded px-2 py-1 text-sm flex-grow"
                        placeholder="Value"
                      />
                      
                      <button 
                        @click="removeCondition(index)" 
                        class="bg-red-500 hover:bg-red-600 text-white px-2 py-1 rounded text-sm"
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                  
                  <div class="mt-2">
                    <button 
                      @click="addConditionToGroup" 
                      class="bg-blue-500 hover:bg-blue-600 text-white px-2 py-1 rounded text-sm"
                    >
                      Add Condition
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="mb-4 flex items-center">
          <input
            id="is_active"
            v-model="newRule.is_active"
            type="checkbox"
            class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label class="ml-2 block text-gray-700 text-sm font-bold" for="is_active">
            Rule is active
          </label>
        </div>
        
        <div class="flex justify-end mt-6">
          <button
            @click="showCreateModal = false"
            class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded mr-2"
          >
            Cancel
          </button>
          <button
            @click="testRuleCriteria"
            class="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded mr-2"
            :disabled="!isRuleValid"
          >
            Test Rule
          </button>
          <button
            @click="createRule"
            class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
            :disabled="!isRuleValid || !newRule.tag_id"
          >
            Create
          </button>
        </div>
      </div>
    </div>
    
    <!-- Test Results Modal -->
    <div v-if="showTestResultsModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-lg p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <h2 class="text-xl font-bold mb-4">Rule Test Results</h2>
        
        <div class="mb-4">
          <p class="text-sm text-gray-600">
            This rule would match <span class="font-bold">{{ testResults.matching_count }}</span> 
            out of <span class="font-bold">{{ testResults.total_devices }}</span> devices.
          </p>
        </div>
        
        <div v-if="testResults.matching_devices && testResults.matching_devices.length > 0" class="border rounded overflow-hidden mb-4">
          <div class="bg-gray-50 px-4 py-2 font-medium">Matching Devices:</div>
          <ul class="divide-y divide-gray-200">
            <li v-for="device in testResults.matching_devices" :key="device.id" class="px-4 py-2 text-sm">
              <div class="font-medium">{{ device.hostname }}</div>
              <div class="text-gray-500">{{ device.ip_address }}</div>
            </li>
          </ul>
        </div>
        
        <div class="flex justify-end">
          <button
            @click="showTestResultsModal = false"
            class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
          >
            Close
          </button>
        </div>
      </div>
    </div>
    
    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
        <h2 class="text-xl font-bold mb-4">Delete Tag Rule</h2>
        
        <p class="mb-6">
          Are you sure you want to delete the rule "<span class="font-semibold">{{ deleteRuleName }}</span>"? 
          This action cannot be undone.
        </p>
        
        <div class="flex justify-end">
          <button
            @click="showDeleteModal = false"
            class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded mr-2"
          >
            Cancel
          </button>
          <button
            @click="deleteRule"
            class="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
          >
            Delete
          </button>
        </div>
      </div>
    </div>

    <!-- Apply Rule Confirmation Modal -->
    <div v-if="showApplyModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
        <h2 class="text-xl font-bold mb-4">Apply Tag Rule</h2>
        
        <p class="mb-6">
          Are you sure you want to apply the rule "<span class="font-semibold">{{ applyRuleName }}</span>"? 
          This will tag all matching devices with the associated tag.
        </p>
        
        <div class="flex justify-end">
          <button
            @click="showApplyModal = false"
            class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded mr-2"
          >
            Cancel
          </button>
          <button
            @click="applyRuleConfirmed"
            class="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
          >
            Apply
          </button>
        </div>
      </div>
    </div>

    <!-- Apply Results Modal -->
    <div v-if="showApplyResultsModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
        <h2 class="text-xl font-bold mb-4">Rule Applied</h2>
        
        <div class="mb-6">
          <p class="mb-2">
            Rule "<span class="font-semibold">{{ applyResults.rule_name }}</span>" was successfully applied.
          </p>
          <p>
            Tagged <span class="font-bold">{{ applyResults.matched_devices }}</span> 
            out of <span class="font-bold">{{ applyResults.total_devices }}</span> devices 
            with tag "<span class="font-semibold">{{ applyResults.tag_name }}</span>".
          </p>
        </div>
        
        <div class="flex justify-end">
          <button
            @click="showApplyResultsModal = false"
            class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import MainLayout from '@/components/MainLayout.vue'
import TagBadge from '@/components/TagBadge.vue'
import { useTagStore } from '@/store/tags'
import { useTagRuleStore } from '@/store/tag-rules'

export default {
  name: 'TagRuleList',
  components: {
    MainLayout,
    TagBadge
  },
  
  setup() {
    const tagStore = useTagStore()
    const tagRuleStore = useTagRuleStore()
    
    const rules = computed(() => tagRuleStore.tagRules)
    const tags = computed(() => tagStore.tags)
    const loading = computed(() => tagRuleStore.loading || tagStore.loading)
    const error = computed(() => tagRuleStore.error || tagStore.error)
    const testResults = computed(() => tagRuleStore.testResults)
    
    const showCreateModal = ref(false)
    const showTestResultsModal = ref(false)
    const showDeleteModal = ref(false)
    const showApplyModal = ref(false)
    const showApplyResultsModal = ref(false)
    
    const applyResults = ref(null)
    
    const newRule = reactive({
      name: '',
      description: '',
      tag_id: '',
      is_active: true,
      rule_criteria: null
    })
    
    // Rule builder object
    const ruleBuilder = reactive({})
    
    const deleteRuleId = ref(null)
    const deleteRuleName = ref('')
    
    const applyRuleId = ref(null)
    const applyRuleName = ref('')
    
    const isRuleValid = computed(() => {
      // For a simple condition
      if (ruleBuilder.field && ruleBuilder.operator && ruleBuilder.value) {
        return true
      }
      
      // For a complex operator
      if (ruleBuilder.type && ruleBuilder.conditions && ruleBuilder.conditions.length > 0) {
        // Check that at least one condition is valid
        return ruleBuilder.conditions.some(c => c.field && c.operator && c.value)
      }
      
      return false
    })
    
    const addSimpleCondition = () => {
      Object.assign(ruleBuilder, {
        field: 'hostname',
        operator: 'contains',
        value: ''
      })
    }
    
    const addComplexOperator = () => {
      Object.assign(ruleBuilder, {
        type: 'and',
        conditions: [
          {
            field: 'hostname',
            operator: 'contains',
            value: ''
          }
        ]
      })
    }
    
    const addConditionToGroup = () => {
      if (ruleBuilder.conditions) {
        ruleBuilder.conditions.push({
          field: 'hostname',
          operator: 'contains',
          value: ''
        })
      }
    }
    
    const removeCondition = (index) => {
      if (ruleBuilder.conditions) {
        ruleBuilder.conditions.splice(index, 1)
        
        // If no conditions left, remove the group
        if (ruleBuilder.conditions.length === 0) {
          clearRuleBuilder()
        }
      }
    }
    
    const clearRuleBuilder = () => {
      Object.keys(ruleBuilder).forEach(key => {
        delete ruleBuilder[key]
      })
    }
    
    const testRuleCriteria = async () => {
      try {
        await tagRuleStore.testRule(ruleBuilder)
        showTestResultsModal.value = true
      } catch (error) {
        console.error('Error testing rule criteria:', error)
        alert(`Failed to test rule criteria: ${error.response?.data?.detail || error.message}`)
      }
    }
    
    const createRule = async () => {
      try {
        newRule.rule_criteria = ruleBuilder
        
        await tagRuleStore.createTagRule({
          name: newRule.name,
          description: newRule.description || null,
          is_active: newRule.is_active,
          tag_id: newRule.tag_id,
          rule_criteria: newRule.rule_criteria
        })
        
        // Reset form
        newRule.name = ''
        newRule.description = ''
        newRule.tag_id = ''
        newRule.is_active = true
        clearRuleBuilder()
        
        // Close modal
        showCreateModal.value = false
      } catch (error) {
        console.error('Error creating tag rule:', error)
        alert(`Failed to create tag rule: ${error.response?.data?.detail || error.message}`)
      }
    }
    
    const editRule = (rule) => {
      // TODO: Implement edit functionality
      alert('Edit functionality will be implemented in a future update')
    }
    
    const confirmDelete = (rule) => {
      deleteRuleId.value = rule.id
      deleteRuleName.value = rule.name
      showDeleteModal.value = true
    }
    
    const deleteRule = async () => {
      try {
        await tagRuleStore.deleteTagRule(deleteRuleId.value)
        
        // Close modal
        showDeleteModal.value = false
      } catch (error) {
        console.error('Error deleting tag rule:', error)
        alert(`Failed to delete tag rule: ${error.response?.data?.detail || error.message}`)
      }
    }
    
    const applyRule = (rule) => {
      if (!rule.is_active) return
      
      applyRuleId.value = rule.id
      applyRuleName.value = rule.name
      showApplyModal.value = true
    }
    
    const applyRuleConfirmed = async () => {
      try {
        // Use the store instead of direct service call
        await tagRuleStore.applyTagRule(applyRuleId.value)
        
        // Close confirmation modal
        showApplyModal.value = false
        
        // Set apply results from store
        applyResults.value = {
          rule_name: applyRuleName.value,
          matched_devices: 'N/A', // This would need to be updated based on the store response
          total_devices: 'N/A',   // This would need to be updated based on the store response
          tag_name: rules.value.find(r => r.id === applyRuleId.value)?.tag_name || 'N/A'
        }
        
        // Show results modal
        showApplyResultsModal.value = true
      } catch (error) {
        showApplyModal.value = false
        console.error('Error applying tag rule:', error)
        alert(`Failed to apply tag rule: ${error.response?.data?.detail || error.message}`)
      }
    }
    
    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      
      const date = new Date(dateString)
      return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      }).format(date)
    }
    
    onMounted(() => {
      // Use store actions instead of undefined functions
      tagRuleStore.fetchTagRules()
      tagStore.fetchTags()
    })
    
    return {
      rules,
      tags,
      loading,
      showCreateModal,
      showTestResultsModal,
      showDeleteModal,
      showApplyModal,
      showApplyResultsModal,
      testResults,
      applyResults,
      newRule,
      ruleBuilder,
      deleteRuleName,
      applyRuleName,
      isRuleValid,
      addSimpleCondition,
      addComplexOperator,
      addConditionToGroup,
      removeCondition,
      clearRuleBuilder,
      testRuleCriteria,
      createRule,
      editRule,
      confirmDelete,
      deleteRule,
      applyRule,
      applyRuleConfirmed,
      formatDate
    }
  }
}
</script> 