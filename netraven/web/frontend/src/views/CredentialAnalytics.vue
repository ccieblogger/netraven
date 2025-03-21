<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">Enhanced Credential Analytics</h1>
      <div class="flex space-x-2">
        <button 
          @click="refreshStats" 
          class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded flex items-center"
          :disabled="loading"
        >
          <i class="fas fa-sync-alt mr-2" :class="{ 'animate-spin': loading }"></i> Refresh
        </button>
        <button
          v-if="isAdmin" 
          @click="openReencryptModal"
          class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded flex items-center"
        >
          <i class="fas fa-key mr-2"></i> Re-encrypt Credentials
        </button>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="loading && !stats" class="flex justify-center items-center h-64">
      <div class="spinner"></div>
    </div>

    <!-- Dashboard content -->
    <div v-else-if="stats" class="space-y-6">
      <!-- Global Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="bg-white rounded-lg shadow p-6">
          <h2 class="text-xl font-medium mb-4">Credential Overview</h2>
          <div class="flex flex-col space-y-4">
            <div class="flex justify-between">
              <span class="text-gray-600">Total Credentials:</span>
              <span class="font-medium">{{ stats.total_count }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">Active Credentials:</span>
              <span class="font-medium">{{ stats.active_count }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">Success Rate:</span>
              <span class="font-medium" :class="successRateColor">{{ formatPercentage(stats.success_rate) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">Failure Rate:</span>
              <span class="font-medium" :class="failureRateColor">{{ formatPercentage(stats.failure_rate) }}</span>
            </div>
          </div>
        </div>

        <!-- Top Performers -->
        <div class="bg-white rounded-lg shadow p-6">
          <h2 class="text-xl font-medium mb-4">Top Performing Credentials</h2>
          <div v-if="!stats.top_performers || stats.top_performers.length === 0" class="text-gray-500 text-center py-4">
            No credential usage data available
          </div>
          <div v-else class="space-y-4">
            <div v-for="credential in stats.top_performers" :key="credential.id" class="border-b pb-2 last:border-0">
              <div class="flex justify-between">
                <span class="font-medium">{{ credential.name }}</span>
                <span class="text-green-600">
                  {{ formatPercentage(credential.success_rate) }}
                </span>
              </div>
              <div class="text-sm text-gray-500">
                {{ credential.username }} | {{ credential.success_count + credential.failure_count }} uses
              </div>
            </div>
          </div>
        </div>

        <!-- Poor Performers -->
        <div class="bg-white rounded-lg shadow p-6">
          <h2 class="text-xl font-medium mb-4">Underperforming Credentials</h2>
          <div v-if="!stats.poor_performers || stats.poor_performers.length === 0" class="text-gray-500 text-center py-4">
            No credential usage data available
          </div>
          <div v-else class="space-y-4">
            <div v-for="credential in stats.poor_performers" :key="credential.id" class="border-b pb-2 last:border-0">
              <div class="flex justify-between">
                <span class="font-medium">{{ credential.name }}</span>
                <span class="text-red-600">
                  {{ formatPercentage(credential.success_rate) }}
                </span>
              </div>
              <div class="text-sm text-gray-500">
                {{ credential.username }} | {{ credential.success_count + credential.failure_count }} uses
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tags Performance Section -->
      <div class="bg-white rounded-lg shadow p-6">
        <h2 class="text-xl font-medium mb-4">Credential Performance by Tag</h2>
        <div v-if="!stats.tag_stats || stats.tag_stats.length === 0" class="text-gray-500 text-center py-4">
          No tag data available
        </div>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tag
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Credentials
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Success Rate
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="tag in stats.tag_stats" :key="tag.id">
                <td class="px-6 py-4 whitespace-nowrap">
                  {{ tag.name }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  {{ tag.credential_count }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span :class="getColorForRate(tag.success_rate)">
                    {{ formatPercentage(tag.success_rate) }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <button 
                    @click="showTagStats(tag.id)"
                    class="text-indigo-600 hover:text-indigo-900 mr-2"
                  >
                    <i class="fas fa-chart-line mr-1"></i> Details
                  </button>
                  <button 
                    @click="getSmartCredentials(tag.id)"
                    class="text-blue-600 hover:text-blue-900 mr-2"
                  >
                    <i class="fas fa-sort-amount-up mr-1"></i> Smart Order
                  </button>
                  <button 
                    @click="optimizePriorities(tag.id)"
                    class="text-green-600 hover:text-green-900"
                  >
                    <i class="fas fa-magic mr-1"></i> Optimize
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="bg-white rounded-lg shadow p-6 text-center">
      <div class="text-gray-500 mb-4">
        <i class="fas fa-chart-line text-5xl mb-4"></i>
        <h3 class="text-xl font-medium">No credential statistics available</h3>
        <p class="text-gray-500 mt-2">Start using credentials to see enhanced analytics.</p>
      </div>
      <button 
        @click="refreshStats" 
        class="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded inline-flex items-center"
      >
        <i class="fas fa-sync-alt mr-2"></i> Refresh
      </button>
    </div>

    <!-- Tag Stats Modal -->
    <div v-if="showingTagModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-lg shadow-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div class="p-6">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-xl font-medium">
              {{ selectedTagStats?.name || 'Tag' }} Performance Details
            </h3>
            <button @click="closeTagModal" class="text-gray-500 hover:text-gray-700">
              <i class="fas fa-times"></i>
            </button>
          </div>
          
          <div v-if="loadingTagStats" class="flex justify-center items-center h-32">
            <div class="spinner"></div>
          </div>
          
          <div v-else-if="selectedTagStats">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div class="bg-gray-50 p-4 rounded">
                <div class="text-sm text-gray-500">Credentials</div>
                <div class="text-2xl font-medium">{{ selectedTagStats.credential_count }}</div>
              </div>
              <div class="bg-gray-50 p-4 rounded">
                <div class="text-sm text-gray-500">Success Rate</div>
                <div class="text-2xl font-medium" :class="getColorForRate(selectedTagStats.success_rate)">
                  {{ formatPercentage(selectedTagStats.success_rate) }}
                </div>
              </div>
              <div class="bg-gray-50 p-4 rounded">
                <div class="text-sm text-gray-500">Total Usage</div>
                <div class="text-2xl font-medium">
                  {{ (selectedTagStats.success_count || 0) + (selectedTagStats.failure_count || 0) }}
                </div>
              </div>
            </div>
            
            <h4 class="font-medium mb-2">Credentials Performance</h4>
            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                    <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Success Rate</th>
                    <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Priority</th>
                    <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Used</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="cred in selectedTagStats.credentials" :key="cred.id" class="border-b">
                    <td class="px-4 py-2">{{ cred.name }}</td>
                    <td class="px-4 py-2">
                      <span :class="getColorForRate(cred.success_rate)">
                        {{ formatPercentage(cred.success_rate) }}
                      </span>
                    </td>
                    <td class="px-4 py-2">{{ cred.priority || 0 }}</td>
                    <td class="px-4 py-2">{{ formatDate(cred.last_used) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
        <div class="bg-gray-50 px-6 py-3 flex justify-end">
          <button @click="closeTagModal" class="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded">
            Close
          </button>
        </div>
      </div>
    </div>

    <!-- Smart Credentials Modal -->
    <div v-if="showingSmartModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-lg shadow-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div class="p-6">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-xl font-medium">
              Smart Credential Selection
            </h3>
            <button @click="closeSmartModal" class="text-gray-500 hover:text-gray-700">
              <i class="fas fa-times"></i>
            </button>
          </div>
          
          <div v-if="loadingSmartCredentials" class="flex justify-center items-center h-32">
            <div class="spinner"></div>
          </div>
          
          <div v-else-if="smartCredentialData">
            <div class="bg-blue-50 border-l-4 border-blue-400 p-4 mb-6">
              <div class="flex">
                <div class="flex-shrink-0">
                  <i class="fas fa-info-circle text-blue-500"></i>
                </div>
                <div class="ml-3">
                  <p class="text-sm text-blue-700">
                    These credentials are ranked using our smart algorithm that considers success rates, 
                    priority settings, and recency of use.
                  </p>
                </div>
              </div>
            </div>
            
            <h4 class="font-medium mb-2">Recommended Order</h4>
            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rank</th>
                    <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                    <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Success Rate</th>
                    <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Score</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(cred, index) in smartCredentialData.credentials" :key="cred.id" class="border-b">
                    <td class="px-4 py-2 font-medium">{{ index + 1 }}</td>
                    <td class="px-4 py-2">{{ cred.name }}</td>
                    <td class="px-4 py-2">
                      <span :class="getColorForRate(cred.success_rate)">
                        {{ formatPercentage(cred.success_rate) }}
                      </span>
                    </td>
                    <td class="px-4 py-2">{{ cred.score.toFixed(2) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            
            <div class="mt-6">
              <h4 class="font-medium mb-2">How We Rank Credentials</h4>
              <div class="bg-gray-50 p-4 rounded">
                <ul class="list-disc list-inside space-y-2 text-sm">
                  <li v-for="(weight, factor) in smartCredentialData.explanation.weights" :key="factor">
                    <span class="font-medium">{{ formatFactorName(factor) }}:</span> {{ weight }} weight
                  </li>
                </ul>
                <p class="mt-4 text-sm">{{ smartCredentialData.explanation.recommendation }}</p>
              </div>
            </div>
          </div>
        </div>
        <div class="bg-gray-50 px-6 py-3 flex justify-end space-x-2">
          <button 
            v-if="smartCredentialData" 
            @click="optimizePriorities(currentTagId)" 
            class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded"
          >
            Apply This Order
          </button>
          <button @click="closeSmartModal" class="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded">
            Close
          </button>
        </div>
      </div>
    </div>
    
    <!-- Re-encrypt Modal -->
    <div v-if="showingReencryptModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-lg shadow-lg max-w-lg w-full">
        <div class="p-6">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-xl font-medium">Re-encrypt Credentials</h3>
            <button 
              @click="closeReencryptModal" 
              class="text-gray-500 hover:text-gray-700"
              :disabled="isReencrypting"
            >
              <i class="fas fa-times"></i>
            </button>
          </div>
          
          <div v-if="reencryptStatus && reencryptStatus.inProgress" class="mb-4">
            <div class="flex items-center justify-center mb-2">
              <div class="spinner mr-3"></div>
              <span>Re-encrypting credentials...</span>
            </div>
          </div>
          
          <div v-else-if="reencryptStatus && !reencryptStatus.inProgress">
            <div 
              class="mb-4 p-4 rounded-md"
              :class="reencryptStatus.success ? 'bg-green-50' : 'bg-red-50'"
            >
              <div class="flex">
                <div class="flex-shrink-0">
                  <i 
                    class="fas mr-3"
                    :class="reencryptStatus.success ? 'fa-check-circle text-green-600' : 'fa-exclamation-circle text-red-600'"
                  ></i>
                </div>
                <div>
                  <h3 class="text-sm font-medium" :class="reencryptStatus.success ? 'text-green-800' : 'text-red-800'">
                    {{ reencryptStatus.message }}
                  </h3>
                  <div class="mt-2 text-sm" :class="reencryptStatus.success ? 'text-green-700' : 'text-red-700'">
                    <ul v-if="reencryptStatus.details" class="list-disc pl-5 space-y-1">
                      <li>Total credentials: {{ reencryptStatus.details.total }}</li>
                      <li>Successfully processed: {{ reencryptStatus.details.successful }}</li>
                      <li>Failed: {{ reencryptStatus.details.failed }}</li>
                      <li v-if="reencryptStatus.details.rollbacks">Rollbacks performed: {{ reencryptStatus.details.rollbacks }}</li>
                    </ul>
                    <p v-if="reencryptStatus.error">{{ reencryptStatus.error }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div v-else>
            <p class="mb-4">This operation will re-encrypt all credentials with the current active encryption key.</p>
            <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
              <div class="flex">
                <div class="flex-shrink-0">
                  <i class="fas fa-exclamation-triangle text-yellow-400"></i>
                </div>
                <div class="ml-3">
                  <p class="text-sm text-yellow-700">
                    This is an administrative operation that may take some time to complete.
                    The process runs in batches to ensure system stability.
                  </p>
                </div>
              </div>
            </div>
            
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-1">Batch Size</label>
              <input 
                type="number" 
                v-model.number="batchSize"
                class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
                min="10"
                max="500"
              />
              <p class="text-xs text-gray-500 mt-1">Number of credentials to process in each batch (10-500)</p>
            </div>
          </div>
        </div>
        
        <div class="bg-gray-50 px-6 py-3 flex justify-end">
          <button
            v-if="!reencryptStatus || !reencryptStatus.inProgress" 
            @click="closeReencryptModal" 
            class="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded mr-2"
          >
            Close
          </button>
          <button
            v-if="(!reencryptStatus || !reencryptStatus.inProgress) && (!reencryptStatus || !reencryptStatus.success)"
            @click="startReencryption"
            class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
            :disabled="isReencrypting"
          >
            Start Re-encryption
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useCredentialStore } from '../store/credential'
import { useAuthStore } from '../store/auth'
import { format } from 'date-fns'

export default {
  name: 'CredentialAnalytics',
  
  setup() {
    const credentialStore = useCredentialStore()
    const authStore = useAuthStore()
    
    const loading = computed(() => credentialStore.loading)
    const stats = ref(null)
    
    // For tag details modal
    const showingTagModal = ref(false)
    const selectedTagStats = ref(null)
    const loadingTagStats = ref(false)
    
    // For smart credentials modal
    const showingSmartModal = ref(false)
    const smartCredentialData = ref(null)
    const loadingSmartCredentials = ref(false)
    const currentTagId = ref(null)
    
    // For re-encryption modal
    const showingReencryptModal = ref(false)
    const batchSize = ref(100)
    const isReencrypting = ref(false)
    const reencryptStatus = computed(() => credentialStore.reencryptStatus)
    
    const isAdmin = computed(() => {
      return authStore.hasRole('admin')
    })
    
    const successRateColor = computed(() => {
      if (!stats.value) return ''
      
      const rate = parseFloat(stats.value.success_rate * 100)
      if (rate >= 80) return 'text-green-600'
      if (rate >= 60) return 'text-yellow-600'
      return 'text-red-600'
    })
    
    const failureRateColor = computed(() => {
      if (!stats.value) return ''
      
      const rate = parseFloat(stats.value.failure_rate * 100)
      if (rate <= 20) return 'text-green-600'
      if (rate <= 40) return 'text-yellow-600'
      return 'text-red-600'
    })
    
    // Fetch stats from API
    const refreshStats = async () => {
      try {
        // Get enhanced stats directly from API
        await credentialStore.fetchDashboardStats()
        stats.value = credentialStore.enhancedStats
      } catch (error) {
        console.error('Error fetching credential statistics:', error)
      }
    }
    
    // Format percentage for display
    const formatPercentage = (value) => {
      if (value === undefined || value === null) return '0.0%'
      
      // Handle values that are already percentages (0-100) or decimal (0-1)
      const numValue = parseFloat(value)
      if (numValue > 1) {
        return numValue.toFixed(1) + '%'
      } else {
        return (numValue * 100).toFixed(1) + '%'
      }
    }
    
    // Get color class based on rate
    const getColorForRate = (rate) => {
      if (rate === undefined || rate === null) return ''
      
      const numRate = parseFloat(rate)
      // Convert to percentage if decimal
      const percentage = numRate > 1 ? numRate : numRate * 100
      
      if (percentage >= 80) return 'text-green-600'
      if (percentage >= 60) return 'text-yellow-600'
      return 'text-red-600'
    }
    
    // Format dates
    const formatDate = (dateString) => {
      if (!dateString) return 'Never'
      try {
        return format(new Date(dateString), 'MMM d, yyyy HH:mm')
      } catch (e) {
        return dateString
      }
    }
    
    // Format factor names for display
    const formatFactorName = (factor) => {
      return factor
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ')
    }
    
    // Show tag details modal
    const showTagStats = async (tagId) => {
      loadingTagStats.value = true
      showingTagModal.value = true
      
      try {
        const tagStats = await credentialStore.fetchTagCredentialStats(tagId)
        selectedTagStats.value = tagStats
      } catch (error) {
        console.error('Error fetching tag stats:', error)
      } finally {
        loadingTagStats.value = false
      }
    }
    
    // Close tag modal
    const closeTagModal = () => {
      showingTagModal.value = false
      selectedTagStats.value = null
    }
    
    // Get smart credentials for a tag
    const getSmartCredentials = async (tagId) => {
      loadingSmartCredentials.value = true
      showingSmartModal.value = true
      currentTagId.value = tagId
      
      try {
        const response = await credentialStore.getSmartCredentialsForTag(tagId)
        smartCredentialData.value = response
      } catch (error) {
        console.error('Error fetching smart credentials:', error)
      } finally {
        loadingSmartCredentials.value = false
      }
    }
    
    // Close smart credentials modal
    const closeSmartModal = () => {
      showingSmartModal.value = false
      smartCredentialData.value = null
      currentTagId.value = null
    }
    
    // Optimize credential priorities for a tag
    const optimizePriorities = async (tagId) => {
      try {
        await credentialStore.optimizeCredentialPriorities(tagId)
        
        // If we're in the smart modal, close it
        if (showingSmartModal.value) {
          closeSmartModal()
        }
        
        // If we're in the tag modal, refresh the tag stats
        if (showingTagModal.value) {
          await showTagStats(tagId)
        }
        
        // Refresh the main stats
        await refreshStats()
      } catch (error) {
        console.error('Error optimizing priorities:', error)
      }
    }
    
    // Open re-encrypt modal
    const openReencryptModal = () => {
      showingReencryptModal.value = true
    }
    
    // Close re-encrypt modal
    const closeReencryptModal = () => {
      if (isReencrypting.value) return
      showingReencryptModal.value = false
    }
    
    // Start re-encryption process
    const startReencryption = async () => {
      isReencrypting.value = true
      
      try {
        await credentialStore.reencryptCredentials(batchSize.value)
      } catch (error) {
        console.error('Error during re-encryption:', error)
      } finally {
        isReencrypting.value = false
      }
    }
    
    onMounted(async () => {
      await refreshStats()
    })
    
    return {
      loading,
      stats,
      isAdmin,
      successRateColor,
      failureRateColor,
      refreshStats,
      formatPercentage,
      getColorForRate,
      formatDate,
      formatFactorName,
      
      // Tag modal
      showingTagModal,
      selectedTagStats,
      loadingTagStats,
      showTagStats,
      closeTagModal,
      
      // Smart credentials modal
      showingSmartModal,
      smartCredentialData,
      loadingSmartCredentials,
      currentTagId,
      getSmartCredentials,
      closeSmartModal,
      
      // Priority optimization
      optimizePriorities,
      
      // Re-encryption
      showingReencryptModal,
      batchSize,
      isReencrypting,
      reencryptStatus,
      openReencryptModal,
      closeReencryptModal,
      startReencryption
    }
  }
}
</script>

<style scoped>
.spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border-left-color: #3b82f6;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style> 