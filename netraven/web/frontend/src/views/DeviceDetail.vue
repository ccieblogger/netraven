<template>
  <MainLayout>
    <div v-if="loading" class="text-center py-8">
      <p>Loading device details...</p>
    </div>
    
    <div v-else-if="!device" class="text-center py-8">
      <p class="text-red-600">Device not found</p>
      <router-link to="/devices" class="text-blue-600 hover:underline mt-4 inline-block">
        Back to Devices
      </router-link>
    </div>
    
    <div v-else>
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-bold">Device: {{ device.hostname }}</h1>
        <div class="flex space-x-2">
          <button 
            @click="backupDevice" 
            class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
            :disabled="backingUp"
          >
            {{ backingUp ? 'Backing up...' : 'Backup Now' }}
          </button>
          <button 
            @click="showEditModal = true" 
            class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded"
          >
            Edit Device
          </button>
        </div>
      </div>
      
      <!-- Device Details -->
      <div class="bg-white rounded-lg shadow p-6 mb-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h2 class="text-lg font-semibold mb-4">Basic Information</h2>
            <div class="space-y-2">
              <div class="flex justify-between">
                <span class="text-gray-600">Hostname:</span>
                <span class="font-medium">{{ device.hostname }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">IP Address:</span>
                <span class="font-medium">{{ device.ip_address }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">Port:</span>
                <span class="font-medium">{{ device.port || 22 }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">Device Type:</span>
                <span class="font-medium">{{ formatDeviceType(device.device_type) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">Status:</span>
                <span 
                  class="font-medium"
                  :class="device.enabled ? 'text-green-600' : 'text-gray-600'"
                >
                  {{ device.enabled ? 'Enabled' : 'Disabled' }}
                </span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">Reachability:</span>
                <div>
                  <span v-if="device.last_reachability_check" 
                    class="font-medium"
                    :class="device.is_reachable ? 'text-green-600' : 'text-red-600'"
                  >
                    {{ device.is_reachable ? 'Reachable' : 'Unreachable' }}
                  </span>
                  <span v-else class="text-gray-500">Unknown</span>
                  <button 
                    @click="checkReachability" 
                    class="ml-2 text-xs text-blue-600 hover:text-blue-900"
                    :disabled="checkingReachability"
                  >
                    {{ checkingReachability ? 'Checking...' : 'Check' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
          
          <div>
            <h2 class="text-lg font-semibold mb-4">Backup Information</h2>
            <div class="space-y-2">
              <div class="flex justify-between">
                <span class="text-gray-600">Last Backup:</span>
                <span class="font-medium">{{ device.last_backup_at ? formatDate(device.last_backup_at) : 'Never' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">Backup Status:</span>
                <span 
                  class="font-medium"
                  :class="device.last_backup_status === 'success' ? 'text-green-600' : 'text-red-600'"
                >
                  {{ device.last_backup_status || 'N/A' }}
                </span>
              </div>
            </div>
            
            <div class="mt-4">
              <h3 class="text-md font-semibold mb-2">Description</h3>
              <p class="text-gray-700">{{ device.description || 'No description provided.' }}</p>
            </div>
            
            <!-- Tags -->
            <div class="mb-6">
              <div class="flex justify-between items-center mb-2">
                <h3 class="text-lg font-medium">Tags</h3>
                <button 
                  @click.stop.prevent="openTagModal" 
                  class="text-sm bg-indigo-600 hover:bg-indigo-700 text-white py-1 px-3 rounded transition-colors"
                >
                  Manage Tags
                </button>
              </div>
              
              <div class="flex flex-wrap gap-2">
                <span 
                  v-for="tag in deviceTags" 
                  :key="tag.id"
                  class="px-3 py-1 rounded-full text-sm"
                  :style="{ backgroundColor: tag.color || '#6366F1', color: 'white' }"
                >
                  {{ formatTagName(tag.name) }}
                </span>
                <span v-if="!deviceTags || deviceTags.length === 0" class="text-gray-500 italic">
                  No tags assigned
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Recent Backups -->
      <div class="bg-white rounded-lg shadow p-6 mb-6">
        <h2 class="text-lg font-semibold mb-4">Device Jobs</h2>
        <div v-if="loadingBackups" class="text-center py-4">
          <p>Loading jobs...</p>
        </div>
        <div v-else-if="deviceBackups.length === 0" class="text-center py-4 text-gray-500">
          <p>No jobs found for this device.</p>
        </div>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Job Name</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Version</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="backup in deviceBackups" :key="backup.id">
                <td class="px-6 py-4 whitespace-nowrap">
                  {{ backup.job_name || 'Device Backup' }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  {{ formatDate(backup.created_at) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                    :class="backup.status === 'complete' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'">
                    {{ backup.status }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  {{ backup.version }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex space-x-2">
                    <router-link :to="`/backups/${backup.id}`" class="text-blue-600 hover:text-blue-900">
                      View
                    </router-link>
                    <button @click="restoreBackup(backup.id)" class="text-green-600 hover:text-green-900">
                      Restore
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      
      <!-- Job Logs -->
      <div class="bg-white rounded-lg shadow p-6">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-lg font-semibold">Job Run History</h2>
          
          <!-- Job Metrics Summary -->
          <div class="flex space-x-3">
            <div class="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
              <span>Success: {{ jobSuccessCount }}</span>
            </div>
            <div class="bg-red-100 text-red-800 px-3 py-1 rounded-full text-sm flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
              </svg>
              <span>Failed: {{ jobFailureCount }}</span>
            </div>
            <div class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd" />
              </svg>
              <span>Total: {{ deviceJobLogs.length }}</span>
            </div>
          </div>
        </div>
        
        <!-- Job Log Filters -->
        <div class="mb-4 p-3 bg-gray-50 rounded-lg">
          <div class="flex flex-wrap items-center gap-3">
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Job Type</label>
              <select 
                v-model="jobFilters.job_type" 
                class="border border-gray-300 rounded-md px-2 py-1 text-sm"
              >
                <option value="">All Types</option>
                <option value="device_backup">Device Backup</option>
                <option value="config_compliance">Config Compliance</option>
                <option value="device_discovery">Device Discovery</option>
              </select>
            </div>
            
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Status</label>
              <select 
                v-model="jobFilters.status" 
                class="border border-gray-300 rounded-md px-2 py-1 text-sm"
              >
                <option value="">All Statuses</option>
                <option value="running">Running</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
              </select>
            </div>
            
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Date Range</label>
              <div class="flex space-x-1">
                <input 
                  type="date" 
                  v-model="jobFilters.start_date" 
                  class="border border-gray-300 rounded-md px-2 py-1 text-sm"
                />
                <input 
                  type="date" 
                  v-model="jobFilters.end_date" 
                  class="border border-gray-300 rounded-md px-2 py-1 text-sm"
                />
              </div>
            </div>
            
            <div class="flex items-end ml-auto">
              <button 
                @click="applyJobFilters" 
                class="bg-blue-600 hover:bg-blue-700 text-white text-sm px-3 py-1 rounded"
              >
                Apply Filters
              </button>
              <button 
                @click="clearJobFilters" 
                class="bg-gray-300 hover:bg-gray-400 text-gray-800 text-sm px-3 py-1 rounded ml-2"
              >
                Clear
              </button>
            </div>
          </div>
        </div>
        
        <!-- Job Logs Table -->
        <div v-if="loadingJobLogs" class="text-center py-4">
          <p>Loading job logs...</p>
        </div>
        
        <div v-else-if="deviceJobLogs.length === 0" class="text-center py-8 text-gray-500">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p class="mt-2">No job logs found for this device.</p>
        </div>
        
        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Job Name
                </th>
                <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Job Type
                </th>
                <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Start Time
                </th>
                <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Duration
                </th>
                <th class="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Result
                </th>
                <th class="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="jobLog in deviceJobLogs" :key="jobLog.id" class="hover:bg-gray-50">
                <td class="px-3 py-3 whitespace-nowrap">
                  {{ jobLog.job_name || getJobName(jobLog.job_type) }}
                </td>
                <td class="px-3 py-3 whitespace-nowrap">
                  <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                    :class="{
                      'bg-blue-100 text-blue-800': jobLog.job_type === 'device_backup',
                      'bg-green-100 text-green-800': jobLog.job_type === 'config_compliance',
                      'bg-purple-100 text-purple-800': jobLog.job_type === 'device_discovery',
                      'bg-gray-100 text-gray-800': !['device_backup', 'config_compliance', 'device_discovery'].includes(jobLog.job_type)
                    }">
                    {{ formatJobType(jobLog.job_type) }}
                  </span>
                </td>
                <td class="px-3 py-3 whitespace-nowrap">
                  <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full"
                    :class="{
                      'bg-yellow-100 text-yellow-800': jobLog.status === 'running',
                      'bg-green-100 text-green-800': jobLog.status === 'completed',
                      'bg-red-100 text-red-800': jobLog.status === 'failed',
                      'bg-gray-100 text-gray-800': !['running', 'completed', 'failed'].includes(jobLog.status)
                    }">
                    {{ jobLog.status }}
                  </span>
                </td>
                <td class="px-3 py-3 whitespace-nowrap text-sm text-gray-500">
                  {{ formatDateTime(jobLog.start_time) }}
                </td>
                <td class="px-3 py-3 whitespace-nowrap text-sm text-gray-500">
                  {{ calculateDuration(jobLog.start_time, jobLog.end_time) }}
                </td>
                <td class="px-3 py-3 whitespace-nowrap text-sm text-gray-500">
                  <span :title="jobLog.result_message">
                    {{ truncateText(jobLog.result_message, 30) || '-' }}
                  </span>
                </td>
                <td class="px-3 py-3 whitespace-nowrap text-right text-sm font-medium">
                  <router-link :to="{
                    path: `/job-logs/${jobLog.id}`,
                    query: { from_device: deviceId, device_name: device.hostname }
                  }" class="text-blue-600 hover:text-blue-900">
                    View Details
                  </router-link>
                </td>
              </tr>
            </tbody>
          </table>
          
          <!-- Pagination Controls -->
          <div class="flex justify-between items-center mt-4">
            <p class="text-sm text-gray-700">
              Showing <span class="font-medium">{{ deviceJobLogs.length }}</span> results
            </p>
            <div class="flex space-x-2">
              <button 
                @click="loadMoreJobLogs" 
                class="bg-white border border-gray-300 text-gray-700 px-3 py-1 rounded text-sm"
                :disabled="!hasMoreJobLogs"
                :class="{'opacity-50 cursor-not-allowed': !hasMoreJobLogs}"
              >
                Load More
              </button>
              <router-link 
                :to="`/job-logs/device/${deviceId}`" 
                class="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
              >
                View All Logs
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Edit Device Modal -->
    <div v-if="showEditModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center">
      <div class="relative bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div class="p-6">
          <h3 class="text-lg font-medium mb-4">Edit Device</h3>
          
          <form @submit.prevent="saveDevice">
            <div class="space-y-4">
              <div>
                <label for="hostname" class="block text-sm font-medium text-gray-700">Hostname</label>
                <input
                  type="text"
                  id="hostname"
                  v-model="deviceForm.hostname"
                  required
                  class="mt-1 block w-full border rounded-md shadow-sm py-2 px-3"
                  :class="{'border-red-300': errors.hostname}"
                >
                <p v-if="errors.hostname" class="mt-1 text-sm text-red-600">{{ errors.hostname }}</p>
              </div>
              
              <div>
                <label for="ip_address" class="block text-sm font-medium text-gray-700">IP Address</label>
                <input
                  type="text"
                  id="ip_address"
                  v-model="deviceForm.ip_address"
                  required
                  class="mt-1 block w-full border rounded-md shadow-sm py-2 px-3"
                  :class="{'border-red-300': errors.ip_address}"
                >
                <p v-if="errors.ip_address" class="mt-1 text-sm text-red-600">{{ errors.ip_address }}</p>
              </div>
              
              <div>
                <label for="device_type" class="block text-sm font-medium text-gray-700">Device Type</label>
                <select
                  id="device_type"
                  v-model="deviceForm.device_type"
                  required
                  class="mt-1 block w-full border rounded-md shadow-sm py-2 px-3"
                  :class="{'border-red-300': errors.device_type}"
                >
                  <option value="cisco_ios">Cisco IOS</option>
                  <option value="juniper_junos">Juniper JunOS</option>
                  <option value="arista_eos">Arista EOS</option>
                </select>
                <p v-if="errors.device_type" class="mt-1 text-sm text-red-600">{{ errors.device_type }}</p>
              </div>
              
              <div>
                <label for="port" class="block text-sm font-medium text-gray-700">Port</label>
                <input
                  type="number"
                  id="port"
                  v-model="deviceForm.port"
                  class="mt-1 block w-full border rounded-md shadow-sm py-2 px-3"
                  :class="{'border-red-300': errors.port}"
                >
                <p v-if="errors.port" class="mt-1 text-sm text-red-600">{{ errors.port }}</p>
              </div>
              
              <div>
                <label for="description" class="block text-sm font-medium text-gray-700">Description</label>
                <textarea
                  id="description"
                  v-model="deviceForm.description"
                  rows="3"
                  class="mt-1 block w-full border rounded-md shadow-sm py-2 px-3"
                  :class="{'border-red-300': errors.description}"
                ></textarea>
                <p v-if="errors.description" class="mt-1 text-sm text-red-600">{{ errors.description }}</p>
              </div>
              
              <div>
                <label for="username" class="block text-sm font-medium text-gray-700">Username</label>
                <input
                  type="text"
                  id="username"
                  v-model="deviceForm.username"
                  placeholder="Leave blank to keep current username"
                  class="mt-1 block w-full border rounded-md shadow-sm py-2 px-3"
                  :class="{'border-red-300': errors.username}"
                >
                <p v-if="errors.username" class="mt-1 text-sm text-red-600">{{ errors.username }}</p>
              </div>
              
              <div>
                <label for="password" class="block text-sm font-medium text-gray-700">Password</label>
                <input
                  type="password"
                  id="password"
                  v-model="deviceForm.password"
                  placeholder="Leave blank to keep current password"
                  class="mt-1 block w-full border rounded-md shadow-sm py-2 px-3"
                  :class="{'border-red-300': errors.password}"
                >
                <p v-if="errors.password" class="mt-1 text-sm text-red-600">{{ errors.password }}</p>
              </div>
              
              <div class="flex items-center">
                <input
                  type="checkbox"
                  id="enabled"
                  v-model="deviceForm.enabled"
                  class="h-4 w-4 text-blue-600 border-gray-300 rounded"
                >
                <label for="enabled" class="ml-2 block text-sm text-gray-900">Device Enabled</label>
              </div>
            </div>
            
            <div class="mt-6 flex justify-end space-x-3">
              <button
                type="button"
                @click="showEditModal = false"
                class="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                :disabled="saving"
                class="bg-blue-600 py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                {{ saving ? 'Saving...' : 'Save Changes' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
    
    <!-- Tag Management Modal -->
    <TagModal 
      :show="showTagModal" 
      :device-id="deviceId"
      @close="closeTagModal"
      @update:tags="updateDeviceTags"
      @open-create-tag="handleOpenCreateTag"
    />
    
    <!-- Create Tag Modal -->
    <teleport to="body">
      <div v-if="showCreateTagModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
        <div class="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md p-6 mx-4 overflow-hidden" @click.stop>
          <button 
            type="button"
            class="absolute top-4 right-4 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200" 
            @click="showCreateTagModal = false"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
          
          <h2 class="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Create New Tag</h2>
          
          <form @submit.prevent="createTag">
            <div class="space-y-4">
              <div>
                <label for="tagName" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Tag Name</label>
                <input
                  type="text"
                  id="tagName"
                  v-model="newTag.name"
                  required
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 text-gray-900 bg-white"
                />
              </div>
              
              <div>
                <label for="tagColor" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Color</label>
                <div class="flex items-center mt-1">
                  <input
                    type="color"
                    id="tagColor"
                    v-model="newTag.color"
                    class="w-10 h-10 rounded border border-gray-300 dark:border-gray-600"
                  />
                  <span class="ml-2 text-sm text-gray-600 dark:text-gray-400">{{ newTag.color }}</span>
                </div>
              </div>
              
              <div>
                <label for="tagDescription" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Description (optional)</label>
                <textarea
                  id="tagDescription"
                  v-model="newTag.description"
                  rows="2"
                  class="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 text-gray-900 bg-white"
                ></textarea>
              </div>
            </div>
            
            <div class="mt-6 flex justify-end space-x-3">
              <button
                type="button"
                @click="showCreateTagModal = false"
                class="py-2 px-4 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
              >
                Cancel
              </button>
              <button
                type="submit"
                :disabled="creatingTag"
                class="py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
              >
                {{ creatingTag ? 'Creating...' : 'Create Tag' }}
              </button>
            </div>
            
            <div 
              v-if="createTagError" 
              class="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-md"
            >
              {{ createTagError }}
            </div>
          </form>
        </div>
      </div>
    </teleport>
  </MainLayout>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Teleport } from 'vue'
import MainLayout from '@/components/MainLayout.vue'
import TagBadge from '@/components/TagBadge.vue'
import { useDeviceStore } from '@/store/devices'
import { useBackupStore } from '@/store/backups'
import { useTagStore } from '@/store/tags'
import { useJobLogStore } from '@/store/job-logs'
import TagModal from '@/components/TagModal.vue'

export default {
  name: 'DeviceDetail',
  components: {
    MainLayout,
    TagBadge,
    TagModal
  },
  props: {
    id: {
      type: String,
      required: false
    }
  },
  setup(props) {
    const route = useRoute()
    const deviceStore = useDeviceStore()
    const backupStore = useBackupStore()
    const tagStore = useTagStore()
    const jobLogStore = useJobLogStore()
    
    const loading = ref(true)
    const loadingBackups = ref(true)
    const backingUp = ref(false)
    const checkingReachability = ref(false)
    const showEditModal = ref(false)
    const saving = ref(false)
    const errors = ref({})
    
    const deviceId = computed(() => props.id || route.params.id)
    
    const device = computed(() => deviceStore.currentDevice)
    
    const deviceBackups = computed(() => {
      return backupStore.backupsByDevice(deviceId.value)
    })

    const deviceForm = ref({
      hostname: '',
      ip_address: '',
      device_type: 'cisco_ios',
      port: 22,
      description: '',
      enabled: true,
      username: '',
      password: ''
    })
    
    const deviceTags = ref([])
    const allTags = computed(() => tagStore.tags)
    const loadingTags = computed(() => tagStore.loading)
    const showTagModal = ref(false)
    const selectedTagId = ref('')
    
    const showCreateTagModal = ref(false)
    const creatingTag = ref(false)
    const createTagError = ref(null)
    const newTag = ref({
      name: '',
      color: '#6366F1', // Default indigo color
      description: ''
    })
    
    // Job logs state
    const loadingJobLogs = ref(false)
    const currentPage = ref(1)
    const pageSize = ref(10)
    const hasMoreJobLogs = ref(false)
    
    const jobFilters = ref({
      job_type: '',
      status: '',
      start_date: '',
      end_date: ''
    })
    
    const deviceJobLogs = ref([])
    
    // Job metrics computed properties
    const jobSuccessCount = computed(() => {
      return deviceJobLogs.value.filter(log => log.status === 'completed').length
    })
    
    const jobFailureCount = computed(() => {
      return deviceJobLogs.value.filter(log => log.status === 'failed').length
    })
    
    onMounted(async () => {
      loading.value = true
      try {
        await deviceStore.fetchDevice(deviceId.value)
        // Initialize the form with current device data
        if (device.value) {
          deviceForm.value = {
            hostname: device.value.hostname,
            ip_address: device.value.ip_address,
            device_type: device.value.device_type,
            port: device.value.port || 22,
            description: device.value.description || '',
            enabled: device.value.enabled,
            username: '',  // We don't get these from the API for security
            password: ''   // Instead, we'll make them optional in the update
          }
        }
      } catch (error) {
        console.error('Failed to fetch device:', error)
      } finally {
        loading.value = false
      }
      
      loadingBackups.value = true
      try {
        await backupStore.fetchBackups({ device_id: deviceId.value })
      } catch (error) {
        console.error('Failed to fetch backups:', error)
      } finally {
        loadingBackups.value = false
      }
      
      // Fetch tags for the device
      await fetchDeviceTags()
      // Fetch all tags
      await tagStore.fetchTags()
      
      // Fetch job logs for the device
      await fetchDeviceJobLogs()
    })
    
    const saveDevice = async () => {
      saving.value = true
      errors.value = {}
      
      try {
        console.log('Saving device with data:', deviceForm.value)
        // Remove empty credentials if not provided (they're optional for updates)
        const updateData = { ...deviceForm.value }
        if (!updateData.username) delete updateData.username
        if (!updateData.password) delete updateData.password
        
        await deviceStore.updateDevice(deviceId.value, updateData)
        showEditModal.value = false
        
        // Refresh the device data
        await deviceStore.fetchDevice(deviceId.value)
      } catch (error) {
        console.error('Failed to save device:', error)
        console.error('Error response:', error.response?.data)
        if (error.response?.data?.detail) {
          // Handle validation errors from the API
          if (Array.isArray(error.response.data.detail)) {
            // Handle FastAPI validation errors
            error.response.data.detail.forEach(err => {
              const field = err.loc[err.loc.length - 1]
              errors.value[field] = err.msg
            })
          } else if (typeof error.response.data.detail === 'object') {
            errors.value = error.response.data.detail
          } else {
            errors.value = { general: error.response.data.detail }
          }
        }
      } finally {
        saving.value = false
      }
    }
    
    const formatDeviceType = (type) => {
      const typeMap = {
        'cisco_ios': 'Cisco IOS',
        'juniper_junos': 'Juniper JunOS',
        'arista_eos': 'Arista EOS'
      }
      return typeMap[type] || type
    }
    
    const formatDate = (dateString) => {
      if (!dateString) return 'Never'
      const date = new Date(dateString)
      return date.toLocaleString()
    }
    
    // Format tag name by removing "tag-" prefix if present
    const formatTagName = (name) => {
      if (!name) return ''
      return name.startsWith('tag-') ? name.substring(4) : name
    }
    
    const backupDevice = async () => {
      backingUp.value = true
      try {
        console.log('Starting device backup process for:', deviceId.value)
        const result = await deviceStore.backupDevice(deviceId.value)
        console.log('Backup result:', result)
        await deviceStore.fetchDevice(deviceId.value)
        await backupStore.fetchBackups({ device_id: deviceId.value })
      } catch (error) {
        console.error('Error backing up device:', error)
        console.error('Error details:', error.response?.data || 'No detailed error information')
      } finally {
        backingUp.value = false
      }
    }
    
    const restoreBackup = async (backupId) => {
      try {
        await backupStore.restoreBackup(backupId)
        // Refresh the device to get updated status
        await deviceStore.fetchDevice(deviceId.value)
      } catch (error) {
        console.error('Failed to restore backup:', error)
      }
    }
    
    const checkReachability = async () => {
      checkingReachability.value = true
      try {
        await deviceStore.checkReachability(deviceId.value)
        await deviceStore.fetchDevice(deviceId.value)
      } catch (error) {
        console.error('Error checking device reachability:', error)
      } finally {
        checkingReachability.value = false
      }
    }
    
    const availableTags = computed(() => {
      if (!deviceTags.value || !allTags.value) return []
      
      // Filter out tags that are already assigned to the device
      return allTags.value.filter(tag => !deviceTags.value.some(dt => dt.id === tag.id))
    })
    
    const addTagToDevice = async (tagId) => {
      if (!tagId) return
      
      try {
        await tagStore.assignTagToDevice(deviceId.value, tagId)
        
        // Refresh device tags
        await fetchDeviceTags()
        // Refresh device data
        await deviceStore.fetchDevice(deviceId.value)
      } catch (error) {
        console.error('Error adding tag to device:', error)
        alert(`Failed to add tag: ${error.response?.data?.detail || error.message}`)
      }
    }
    
    const removeTagFromDevice = async (tagId) => {
      if (!tagId) return
      
      try {
        await tagStore.removeTagFromDevice(deviceId.value, tagId)
        
        // Refresh device tags
        await fetchDeviceTags()
        // Refresh device data
        await deviceStore.fetchDevice(deviceId.value)
      } catch (error) {
        console.error('Error removing tag from device:', error)
        alert(`Failed to remove tag: ${error.response?.data?.detail || error.message}`)
      }
    }
    
    const fetchDeviceTags = async () => {
      if (!deviceId.value) return
      
      try {
        const tags = await tagStore.fetchTagsForDevice(deviceId.value)
        deviceTags.value = tags
      } catch (error) {
        console.error('Failed to fetch device tags:', error)
      }
    }
    
    const openTagModal = (event) => {
      if (event) {
        event.preventDefault()
        event.stopPropagation()
      }
      showTagModal.value = true
      return false // Prevent link navigation
    }
    
    const closeTagModal = () => {
      console.log('Closing tag modal');
      showTagModal.value = false;
    }
    
    const updateDeviceTags = (tags) => {
      console.log('Updating device tags:', tags);
      deviceTags.value = tags || [];
    }
    
    const createTag = async () => {
      if (!newTag.value.name) {
        console.error('Tag name is required');
        createTagError.value = 'Tag name is required';
        return;
      }
      
      console.log('Creating new tag:', newTag.value);
      creatingTag.value = true;
      createTagError.value = null;
      
      try {
        // Create the tag
        const tag = await tagStore.createTag(newTag.value);
        console.log('Tag created successfully:', tag);
        
        // Close the modal
        showCreateTagModal.value = false;
        
        // Reset form
        newTag.value = {
          name: '',
          color: '#6366F1',
          description: ''
        };
        
        // Refresh tags list
        await tagStore.fetchTags();
        
        // If device id exists, assign the tag to the device
        if (deviceId.value && tag) {
          await tagStore.assignTagToDevice(deviceId.value, tag.id);
          await fetchDeviceTags();
        }
        
        // If the tag modal is open, close it and reopen to refresh
        if (showTagModal.value) {
          showTagModal.value = false;
          setTimeout(() => {
            showTagModal.value = true;
          }, 100);
        }
      } catch (error) {
        console.error('Failed to create tag:', error);
        createTagError.value = 'Failed to create tag. Please try again.';
      } finally {
        creatingTag.value = false;
      }
    }
    
    const handleOpenCreateTag = () => {
      // Add a small delay before showing the create tag modal
      // This ensures the TagModal is fully closed before opening the new modal
      setTimeout(() => {
        showCreateTagModal.value = true
      }, 50)
    }
    
    const fetchDeviceJobLogs = async () => {
      if (!deviceId.value) return
      
      loadingJobLogs.value = true
      try {
        // Reset pagination when fetching new logs
        currentPage.value = 1
        
        // Set device_id filter
        const params = {
          device_id: deviceId.value,
          ...jobFilters.value,
          page: currentPage.value,
          page_size: pageSize.value
        }
        
        // Remove empty filters
        Object.keys(params).forEach(key => {
          if (!params[key]) delete params[key]
        })
        
        const jobLogs = await jobLogStore.fetchJobLogs(params)
        deviceJobLogs.value = jobLogs
        
        // Check if there are more logs to load
        hasMoreJobLogs.value = jobLogs.length === pageSize.value
      } catch (error) {
        console.error('Failed to fetch device job logs:', error)
      } finally {
        loadingJobLogs.value = false
      }
    }
    
    const loadMoreJobLogs = async () => {
      if (!deviceId.value || !hasMoreJobLogs.value) return
      
      loadingJobLogs.value = true
      try {
        // Increment page number
        currentPage.value++
        
        // Set device_id filter
        const params = {
          device_id: deviceId.value,
          ...jobFilters.value,
          page: currentPage.value,
          page_size: pageSize.value
        }
        
        // Remove empty filters
        Object.keys(params).forEach(key => {
          if (!params[key]) delete params[key]
        })
        
        const jobLogs = await jobLogStore.fetchJobLogs(params)
        
        // Append new logs to existing ones
        deviceJobLogs.value = [...deviceJobLogs.value, ...jobLogs]
        
        // Check if there are more logs to load
        hasMoreJobLogs.value = jobLogs.length === pageSize.value
      } catch (error) {
        console.error('Failed to load more device job logs:', error)
      } finally {
        loadingJobLogs.value = false
      }
    }
    
    const applyJobFilters = () => {
      fetchDeviceJobLogs()
    }
    
    const clearJobFilters = () => {
      jobFilters.value = {
        job_type: '',
        status: '',
        start_date: '',
        end_date: ''
      }
      fetchDeviceJobLogs()
    }
    
    const formatJobType = (type) => {
      const typeMap = {
        'device_backup': 'Backup',
        'config_compliance': 'Compliance',
        'device_discovery': 'Discovery',
        'system_maintenance': 'Maintenance'
      }
      return typeMap[type] || type
    }
    
    const formatDateTime = (dateString) => {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      return date.toLocaleString()
    }
    
    const calculateDuration = (startTime, endTime) => {
      if (!startTime) return 'N/A'
      
      const start = new Date(startTime)
      const end = endTime ? new Date(endTime) : new Date()
      
      const durationMs = end - start
      const seconds = Math.floor(durationMs / 1000)
      
      if (seconds < 60) {
        return `${seconds} sec${seconds !== 1 ? 's' : ''}`
      }
      
      const minutes = Math.floor(seconds / 60)
      if (minutes < 60) {
        return `${minutes} min${minutes !== 1 ? 's' : ''}`
      }
      
      const hours = Math.floor(minutes / 60)
      const remainingMinutes = minutes % 60
      return `${hours} hr${hours !== 1 ? 's' : ''} ${remainingMinutes} min${remainingMinutes !== 1 ? 's' : ''}`
    }
    
    const truncateText = (text, maxLength) => {
      if (!text) return ''
      if (text.length <= maxLength) return text
      return `${text.substring(0, maxLength)}...`
    }
    
    const getJobName = (jobType) => {
      // Generate a job name based on the job type
      switch(jobType) {
        case 'device_backup':
          return 'Device Backup Job';
        case 'config_compliance':
          return 'Configuration Compliance Job';
        case 'device_discovery':
          return 'Device Discovery Job';
        default:
          return 'Maintenance Job';
      }
    }
    
    return {
      device,
      loading,
      deviceBackups,
      loadingBackups,
      backingUp,
      showEditModal,
      deviceForm,
      saving,
      errors,
      formatDeviceType,
      formatDate,
      formatTagName,
      backupDevice,
      restoreBackup,
      saveDevice,
      deviceTags,
      loadingTags,
      showTagModal,
      openTagModal,
      closeTagModal,
      updateDeviceTags,
      availableTags,
      addTagToDevice,
      removeTagFromDevice,
      showCreateTagModal,
      creatingTag,
      createTagError,
      newTag,
      createTag,
      deviceId,
      handleOpenCreateTag,
      checkingReachability,
      checkReachability,
      loadingJobLogs,
      deviceJobLogs,
      jobFilters,
      jobSuccessCount,
      jobFailureCount,
      hasMoreJobLogs,
      fetchDeviceJobLogs,
      loadMoreJobLogs,
      applyJobFilters,
      clearJobFilters,
      formatJobType,
      formatDateTime,
      calculateDuration,
      truncateText,
      getJobName
    }
  }
}
</script> 