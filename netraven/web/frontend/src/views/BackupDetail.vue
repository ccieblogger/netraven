<template>
  <MainLayout>
    <div v-if="loading" class="text-center py-8">
      <p>Loading backup details...</p>
    </div>
    
    <div v-else-if="!backup" class="text-center py-8">
      <p class="text-red-600">Backup not found</p>
      <router-link to="/backups" class="text-blue-600 hover:underline mt-4 inline-block">
        Back to Backups
      </router-link>
    </div>
    
    <div v-else class="space-y-6">
      <div class="flex justify-between items-center">
        <h1 class="text-2xl font-bold">Backup Details</h1>
        <div class="flex space-x-3">
          <button 
            @click="restoreBackup" 
            class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded"
            :disabled="backup.status !== 'success'"
          >
            Restore Backup
          </button>
          <router-link 
            to="/backups" 
            class="bg-gray-200 hover:bg-gray-300 text-gray-800 px-4 py-2 rounded"
          >
            Back to List
          </router-link>
        </div>
      </div>
      
      <!-- Backup Information -->
      <div class="bg-white rounded-lg shadow p-6">
        <h2 class="text-xl font-semibold mb-4">Backup Information</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <dl class="space-y-3">
              <div class="flex justify-between">
                <dt class="text-gray-600">Device:</dt>
                <dd class="font-medium">{{ backup.device_name || backup.device_id }}</dd>
              </div>
              <div class="flex justify-between">
                <dt class="text-gray-600">Created:</dt>
                <dd class="font-medium">{{ formatDate(backup.created_at) }}</dd>
              </div>
              <div class="flex justify-between">
                <dt class="text-gray-600">Status:</dt>
                <dd>
                  <span 
                    class="px-2 py-1 text-xs font-semibold rounded-full"
                    :class="statusClass(backup.status)"
                  >
                    {{ backup.status }}
                  </span>
                </dd>
              </div>
              <div class="flex justify-between">
                <dt class="text-gray-600">Storage Type:</dt>
                <dd class="font-medium">{{ backup.storage_type || 'Local' }}</dd>
              </div>
              <div class="flex justify-between">
                <dt class="text-gray-600">Size:</dt>
                <dd class="font-medium">{{ backup.size ? formatSize(backup.size) : 'Unknown' }}</dd>
              </div>
            </dl>
          </div>
          <div v-if="backup.metadata">
            <h3 class="text-lg font-semibold mb-2">Metadata</h3>
            <div class="bg-gray-50 p-3 rounded">
              <pre class="text-xs overflow-x-auto">{{ JSON.stringify(backup.metadata, null, 2) }}</pre>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Backup Content -->
      <div class="bg-white rounded-lg shadow p-6">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-xl font-semibold">Configuration Content</h2>
          <button 
            @click="copyToClipboard" 
            class="text-blue-600 hover:text-blue-800 text-sm flex items-center"
          >
            <span>Copy to clipboard</span>
          </button>
        </div>
        
        <div v-if="!backup.content" class="text-center py-6 text-gray-500">
          <p>Configuration content not available.</p>
        </div>
        <div v-else class="bg-gray-50 p-4 rounded">
          <pre class="text-sm overflow-x-auto h-96">{{ backup.content }}</pre>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MainLayout from '../components/MainLayout.vue'
import { useBackupStore } from '../store/backups'

export default {
  name: 'BackupDetail',
  components: {
    MainLayout
  },
  
  setup() {
    const route = useRoute()
    const router = useRouter()
    const backupStore = useBackupStore()
    
    const loading = ref(true)
    const backupId = computed(() => route.params.id)
    const backup = ref(null)
    
    const fetchBackup = async () => {
      if (!backupId.value) return
      
      loading.value = true
      try {
        await backupStore.fetchBackup(backupId.value)
        backup.value = backupStore.currentBackup
      } catch (error) {
        console.error('Failed to fetch backup:', error)
      } finally {
        loading.value = false
      }
    }
    
    const formatDate = (dateString) => {
      if (!dateString) return 'Unknown'
      const date = new Date(dateString)
      return date.toLocaleString()
    }
    
    const formatSize = (sizeInBytes) => {
      if (!sizeInBytes) return 'Unknown'
      
      const units = ['B', 'KB', 'MB', 'GB']
      let size = sizeInBytes
      let unitIndex = 0
      
      while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024
        unitIndex++
      }
      
      return `${size.toFixed(1)} ${units[unitIndex]}`
    }
    
    const statusClass = (status) => {
      switch (status) {
        case 'success':
          return 'bg-green-100 text-green-800'
        case 'failed':
          return 'bg-red-100 text-red-800'
        case 'in_progress':
          return 'bg-yellow-100 text-yellow-800'
        default:
          return 'bg-gray-100 text-gray-800'
      }
    }
    
    const restoreBackup = async () => {
      if (!backup.value || backup.value.status !== 'success') return
      
      try {
        await backupStore.restoreBackup(backupId.value)
        // Optionally show success message
      } catch (error) {
        console.error('Failed to restore backup:', error)
      }
    }
    
    const copyToClipboard = () => {
      if (!backup.value?.content) return
      
      navigator.clipboard.writeText(backup.value.content)
        .then(() => {
          // Optionally show a copied message
          console.log('Configuration copied to clipboard')
        })
        .catch(err => {
          console.error('Failed to copy configuration:', err)
        })
    }
    
    onMounted(() => {
      fetchBackup()
    })
    
    return {
      loading,
      backup,
      formatDate,
      formatSize,
      statusClass,
      restoreBackup,
      copyToClipboard
    }
  }
}
</script> 