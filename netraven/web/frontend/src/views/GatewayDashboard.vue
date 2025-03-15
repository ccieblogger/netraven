<template>
  <MainLayout>
    <div class="gateway-dashboard">
      <h1 class="text-2xl font-semibold mb-6">Device Gateway Dashboard</h1>
      
      <!-- Error message -->
      <div v-if="error" class="bg-red-50 border-l-4 border-red-500 p-4 mb-6">
        <div class="flex">
          <div class="flex-shrink-0">
            <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="ml-3">
            <h3 class="text-sm font-medium text-red-800">Gateway Error</h3>
            <div class="mt-2 text-sm text-red-700">
              <p>{{ error }}</p>
              <button 
                @click="loadData" 
                class="mt-2 bg-red-200 hover:bg-red-300 text-red-800 px-3 py-1 rounded"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Loading indicator -->
      <div v-if="loading" class="text-center py-8">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p class="mt-4 text-gray-600">Loading gateway data...</p>
      </div>

      <!-- Gateway status and metrics -->
      <div v-if="!loading && !error" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <!-- Status Card -->
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex justify-between items-center mb-4">
            <h2 class="text-xl font-semibold">Gateway Status</h2>
            <div 
              :class="gatewayStatus === 'running' ? 'bg-green-500' : 'bg-red-500'" 
              class="w-3 h-3 rounded-full"
            ></div>
          </div>
          <div class="space-y-2">
            <div class="flex justify-between">
              <span class="text-gray-600">Status:</span>
              <span class="font-medium">{{ gatewayStatus || 'Unknown' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">Version:</span>
              <span class="font-medium">{{ gatewayVersion || 'Unknown' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">Uptime:</span>
              <span class="font-medium">{{ gatewayUptime || 'Unknown' }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">Connected Devices:</span>
              <span class="font-medium">{{ connectedDevices || 0 }}</span>
            </div>
          </div>
        </div>

        <!-- Request Metrics Card -->
        <div class="bg-white rounded-lg shadow p-6">
          <h2 class="text-xl font-semibold mb-4">Request Metrics</h2>
          <div class="space-y-2">
            <div class="flex justify-between">
              <span class="text-gray-600">Total Requests:</span>
              <span class="font-medium">{{ metrics.total_requests || 0 }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">Successful:</span>
              <span class="font-medium">{{ metrics.successful_requests || 0 }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">Failed:</span>
              <span class="font-medium">{{ metrics.failed_requests || 0 }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">Success Rate:</span>
              <span class="font-medium">{{ successRate }}%</span>
            </div>
          </div>
        </div>

        <!-- Performance Metrics Card -->
        <div class="bg-white rounded-lg shadow p-6">
          <h2 class="text-xl font-semibold mb-4">Performance</h2>
          <div class="space-y-2">
            <div class="flex justify-between">
              <span class="text-gray-600">Avg Response Time:</span>
              <span class="font-medium">{{ metrics.avg_response_time?.toFixed(2) || 0 }} ms</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">Active Connections:</span>
              <span class="font-medium">{{ metrics.active_connections || 0 }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">Total Connections:</span>
              <span class="font-medium">{{ metrics.total_connections || 0 }}</span>
            </div>
          </div>
        </div>

        <!-- Error Metrics Card -->
        <div class="bg-white rounded-lg shadow p-6">
          <h2 class="text-xl font-semibold mb-4">Errors</h2>
          <div v-if="Object.keys(metrics.error_counts || {}).length === 0" class="text-gray-500 italic">
            No errors recorded
          </div>
          <div v-else class="space-y-2">
            <div 
              v-for="(count, type) in metrics.error_counts" 
              :key="type" 
              class="flex justify-between"
            >
              <span class="text-gray-600">{{ formatErrorType(type) }}:</span>
              <span class="font-medium">{{ count }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Device Metrics -->
      <div v-if="!loading && !error && hasDeviceMetrics" class="bg-white rounded-lg shadow p-6 mb-8">
        <h2 class="text-xl font-semibold mb-4">Device Metrics</h2>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Device
                </th>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Connections
                </th>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Success Rate
                </th>
                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Connected
                </th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="(data, device) in metrics.device_metrics" :key="device">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {{ device }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ data.connection_count || 0 }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ calculateDeviceSuccessRate(data) }}%
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ formatLastConnected(data.last_connected) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex space-x-4 mb-8">
        <button 
          @click="loadData" 
          class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
        >
          Refresh Data
        </button>
        <button 
          @click="resetMetrics" 
          class="bg-gray-200 hover:bg-gray-300 text-gray-800 px-4 py-2 rounded"
        >
          Reset Metrics
        </button>
      </div>

      <!-- Gateway Configuration -->
      <div v-if="!loading && !error && gatewayConfig" class="bg-white rounded-lg shadow p-6">
        <h2 class="text-xl font-semibold mb-4">Gateway Configuration</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div v-for="(value, key) in gatewayConfig" :key="key" class="flex justify-between">
            <span class="text-gray-600">{{ formatConfigKey(key) }}:</span>
            <span class="font-medium">{{ formatConfigValue(key, value) }}</span>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script>
import MainLayout from '@/components/layouts/MainLayout.vue';
import api from '@/api/api';

export default {
  name: 'GatewayDashboard',
  components: {
    MainLayout
  },
  data() {
    return {
      loading: true,
      error: null,
      gatewayStatus: null,
      gatewayVersion: null,
      gatewayUptime: null,
      connectedDevices: 0,
      metrics: {
        total_requests: 0,
        successful_requests: 0,
        failed_requests: 0,
        avg_response_time: 0,
        active_connections: 0,
        total_connections: 0,
        error_counts: {},
        device_metrics: {}
      },
      gatewayConfig: null,
      refreshInterval: null
    };
  },
  computed: {
    successRate() {
      if (!this.metrics.total_requests) return '0';
      return ((this.metrics.successful_requests / this.metrics.total_requests) * 100).toFixed(1);
    },
    hasDeviceMetrics() {
      return this.metrics.device_metrics && Object.keys(this.metrics.device_metrics).length > 0;
    }
  },
  methods: {
    async loadData() {
      this.loading = true;
      this.error = null;

      try {
        // Get gateway status
        const statusData = await api.getGatewayStatus();
        if (statusData.error) {
          throw new Error(statusData.error);
        }

        this.gatewayStatus = statusData.status;
        this.gatewayVersion = statusData.version;
        this.gatewayUptime = statusData.uptime;
        this.connectedDevices = statusData.connected_devices;
        
        // Get detailed metrics
        const metricsData = await api.getGatewayMetrics();
        if (metricsData.error) {
          throw new Error(metricsData.error);
        }
        
        this.metrics = metricsData;

        // Get gateway configuration
        const configData = await api.getGatewayConfig();
        if (configData.error) {
          console.error('Error loading gateway config:', configData.error);
          // Don't throw here, just log the error
        } else {
          this.gatewayConfig = configData;
        }
      } catch (err) {
        console.error('Error loading gateway data:', err);
        this.error = err.message || 'Failed to load gateway data. The gateway service may be unavailable.';
      } finally {
        this.loading = false;
      }
    },
    async resetMetrics() {
      try {
        const result = await api.resetGatewayMetrics();
        if (result.error) {
          throw new Error(result.error);
        }
        // Reload data after reset
        await this.loadData();
      } catch (err) {
        console.error('Error resetting metrics:', err);
        this.error = err.message || 'Failed to reset metrics';
      }
    },
    formatErrorType(type) {
      // Convert snake_case to Title Case
      return type
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
    },
    calculateDeviceSuccessRate(deviceData) {
      if (!deviceData.connection_count) return '0';
      return ((deviceData.successful_connections / deviceData.connection_count) * 100).toFixed(1);
    },
    formatLastConnected(timestamp) {
      if (!timestamp) return 'Never';
      
      // If timestamp is a number, convert to Date
      const date = typeof timestamp === 'number' 
        ? new Date(timestamp * 1000) 
        : new Date(timestamp);
      
      // Check if date is valid
      if (isNaN(date.getTime())) return 'Invalid date';
      
      // Format date
      return date.toLocaleString();
    },
    formatConfigKey(key) {
      // Convert snake_case to Title Case
      return key
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
    },
    formatConfigValue(key, value) {
      // Handle special cases
      if (key === 'api_key' || key === 'jwt_secret') {
        return '********';
      }
      
      // Format boolean values
      if (typeof value === 'boolean') {
        return value ? 'Enabled' : 'Disabled';
      }
      
      // Format numeric values
      if (typeof value === 'number') {
        if (key.includes('timeout')) {
          return `${value} seconds`;
        }
        if (key.includes('delay')) {
          return `${value} seconds`;
        }
      }
      
      return value;
    },
    startAutoRefresh() {
      // Refresh data every 30 seconds
      this.refreshInterval = setInterval(() => {
        this.loadData();
      }, 30000);
    },
    stopAutoRefresh() {
      if (this.refreshInterval) {
        clearInterval(this.refreshInterval);
        this.refreshInterval = null;
      }
    }
  },
  mounted() {
    this.loadData();
    this.startAutoRefresh();
  },
  beforeUnmount() {
    this.stopAutoRefresh();
  }
};
</script> 