<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">Credential Dashboard</h1>
      <div class="flex space-x-2">
        <button 
          @click="refreshStats" 
          class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded flex items-center"
          :disabled="loading"
        >
          <i class="fas fa-sync-alt mr-2" :class="{ 'animate-spin': loading }"></i> Refresh
        </button>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="loading && !stats" class="flex justify-center items-center h-64">
      <div class="spinner"></div>
    </div>

    <!-- Dashboard content -->
    <div v-else-if="stats" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <!-- Summary card -->
      <div class="bg-white rounded-lg shadow p-6">
        <h2 class="text-xl font-medium mb-4">Credential Summary</h2>
        <div class="flex flex-col space-y-4">
          <div class="flex justify-between">
            <span class="text-gray-600">Total Credentials:</span>
            <span class="font-medium">{{ stats.totalCredentials }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-600">Successful Authentications:</span>
            <span class="font-medium text-green-600">{{ stats.totalSuccess }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-600">Failed Authentications:</span>
            <span class="font-medium text-red-600">{{ stats.totalFailure }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-600">Success Rate:</span>
            <span class="font-medium" :class="successRateColor">{{ stats.successRate }}%</span>
          </div>
        </div>
      </div>

      <!-- Most successful credentials -->
      <div class="bg-white rounded-lg shadow p-6">
        <h2 class="text-xl font-medium mb-4">Most Successful Credentials</h2>
        <div v-if="stats.mostSuccessful.length === 0" class="text-gray-500 text-center py-4">
          No credential usage data available
        </div>
        <div v-else class="space-y-4">
          <div v-for="credential in stats.mostSuccessful" :key="credential.id" class="border-b pb-2 last:border-0">
            <div class="flex justify-between">
              <span class="font-medium">{{ credential.name }}</span>
              <span class="text-green-600">
                {{ calculateSuccessRate(credential) }}%
              </span>
            </div>
            <div class="text-sm text-gray-500">
              {{ credential.username }} | {{ formatTotalUsage(credential) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Least successful credentials -->
      <div class="bg-white rounded-lg shadow p-6">
        <h2 class="text-xl font-medium mb-4">Least Successful Credentials</h2>
        <div v-if="stats.leastSuccessful.length === 0" class="text-gray-500 text-center py-4">
          No credential usage data available
        </div>
        <div v-else class="space-y-4">
          <div v-for="credential in stats.leastSuccessful" :key="credential.id" class="border-b pb-2 last:border-0">
            <div class="flex justify-between">
              <span class="font-medium">{{ credential.name }}</span>
              <span class="text-red-600">
                {{ calculateSuccessRate(credential) }}%
              </span>
            </div>
            <div class="text-sm text-gray-500">
              {{ credential.username }} | {{ formatTotalUsage(credential) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Device type breakdown -->
      <div class="bg-white rounded-lg shadow p-6 lg:col-span-3">
        <h2 class="text-xl font-medium mb-4">Credentials by Device Type</h2>
        <div v-if="Object.keys(stats.deviceTypes).length === 0" class="text-gray-500 text-center py-4">
          No device type data available
        </div>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Device Type
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Credentials
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Success
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Failure
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Success Rate
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="(data, deviceType) in stats.deviceTypes" :key="deviceType">
                <td class="px-6 py-4 whitespace-nowrap">
                  {{ deviceType }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  {{ data.count }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-green-600">
                  {{ data.success }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-red-600">
                  {{ data.failure }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  {{ calculateDeviceTypeSuccessRate(data) }}%
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
        <i class="fas fa-chart-bar text-5xl mb-4"></i>
        <h3 class="text-xl font-medium">No credential statistics available</h3>
        <p class="text-gray-500 mt-2">Start using credentials to see usage statistics.</p>
      </div>
      <button 
        @click="refreshStats" 
        class="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded inline-flex items-center"
      >
        <i class="fas fa-sync-alt mr-2"></i> Refresh
      </button>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useCredentialStore } from '../store/credential'

export default {
  name: 'CredentialDashboard',
  
  setup() {
    const credentialStore = useCredentialStore()
    
    const loading = computed(() => credentialStore.loading)
    const stats = ref(null)
    
    const successRateColor = computed(() => {
      if (!stats.value) return ''
      
      const rate = parseFloat(stats.value.successRate)
      if (rate >= 80) return 'text-green-600'
      if (rate >= 60) return 'text-yellow-600'
      return 'text-red-600'
    })
    
    const refreshStats = async () => {
      try {
        const dashboardStats = await credentialStore.fetchDashboardStats()
        stats.value = dashboardStats
      } catch (error) {
        console.error('Error fetching dashboard stats:', error)
      }
    }
    
    const calculateSuccessRate = (credential) => {
      const total = credential.success_count + credential.failure_count
      if (total === 0) return '0.0'
      
      return ((credential.success_count / total) * 100).toFixed(1)
    }
    
    const formatTotalUsage = (credential) => {
      const total = credential.success_count + credential.failure_count
      return `${total} total attempts`
    }
    
    const calculateDeviceTypeSuccessRate = (data) => {
      const total = data.success + data.failure
      if (total === 0) return '0.0'
      
      return ((data.success / total) * 100).toFixed(1)
    }
    
    onMounted(async () => {
      await refreshStats()
    })
    
    return {
      loading,
      stats,
      successRateColor,
      refreshStats,
      calculateSuccessRate,
      formatTotalUsage,
      calculateDeviceTypeSuccessRate
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