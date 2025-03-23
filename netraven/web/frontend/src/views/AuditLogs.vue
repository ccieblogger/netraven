<!-- Audit Logs View Component -->
<template>
  <div class="audit-logs-container">
    <h1 class="text-2xl font-semibold mb-4">
      <font-awesome-icon :icon="['fas', 'clipboard-list']" class="mr-2" />
      Security Audit Logs
    </h1>
    
    <!-- Filters Panel -->
    <div class="bg-white shadow rounded-lg p-4 mb-6">
      <div class="flex flex-wrap -mx-2">
        <div class="w-full md:w-1/2 lg:w-1/4 px-2 mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-1">Event Type</label>
          <select 
            v-model="filters.eventType" 
            class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          >
            <option value="">All Types</option>
            <option value="auth">Authentication</option>
            <option value="admin">Administration</option>
            <option value="key">Key Management</option>
            <option value="data">Data Access</option>
          </select>
        </div>
        
        <div class="w-full md:w-1/2 lg:w-1/4 px-2 mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-1">Event Name</label>
          <input 
            type="text" 
            v-model="filters.eventName" 
            placeholder="e.g. login, token_refresh" 
            class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          />
        </div>
        
        <div class="w-full md:w-1/2 lg:w-1/4 px-2 mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-1">User/Actor</label>
          <input 
            type="text" 
            v-model="filters.actorId" 
            placeholder="Username" 
            class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          />
        </div>
        
        <div class="w-full md:w-1/2 lg:w-1/4 px-2 mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-1">Status</label>
          <select 
            v-model="filters.status" 
            class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="success">Success</option>
            <option value="failure">Failure</option>
            <option value="error">Error</option>
            <option value="warning">Warning</option>
          </select>
        </div>
        
        <div class="w-full md:w-1/2 lg:w-1/4 px-2 mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-1">Date Range</label>
          <div class="flex space-x-2">
            <input 
              type="date" 
              v-model="filters.startDate" 
              class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            />
            <input 
              type="date" 
              v-model="filters.endDate" 
              class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            />
          </div>
        </div>
        
        <div class="w-full px-2 flex justify-end mb-4">
          <button 
            @click="applyFilters" 
            class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
          >
            <font-awesome-icon :icon="['fas', 'filter']" class="mr-2" />
            Apply Filters
          </button>
          
          <button 
            @click="resetFilters" 
            class="ml-2 px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-md transition-colors"
          >
            <font-awesome-icon :icon="['fas', 'undo']" class="mr-2" />
            Reset
          </button>
        </div>
      </div>
    </div>
    
    <!-- Results Table -->
    <div class="bg-white shadow rounded-lg overflow-hidden">
      <div v-if="loading" class="flex justify-center items-center py-16">
        <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
      
      <div v-else-if="error" class="py-8 px-4 text-center">
        <div class="text-red-500 mb-2">
          <font-awesome-icon :icon="['fas', 'exclamation-circle']" class="text-2xl" />
        </div>
        <p class="text-gray-700">{{ error }}</p>
        <button 
          @click="fetchAuditLogs" 
          class="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
        >
          Try Again
        </button>
      </div>
      
      <div v-else-if="auditLogs.length === 0" class="py-8 px-4 text-center">
        <div class="text-gray-400 mb-2">
          <font-awesome-icon :icon="['fas', 'search']" class="text-2xl" />
        </div>
        <p class="text-gray-700">No audit logs found matching the current filters.</p>
      </div>
      
      <div v-else>
        <table class="w-full">
          <thead class="bg-gray-50 border-b">
            <tr>
              <th class="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
              <th class="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Event</th>
              <th class="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
              <th class="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
              <th class="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th class="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            <tr v-for="log in auditLogs" :key="log.id" class="hover:bg-gray-50">
              <td class="py-3 px-4 text-sm text-gray-500">
                {{ formatDate(log.created_at) }}
              </td>
              <td class="py-3 px-4">
                <div class="flex items-center">
                  <div :class="getEventTypeClass(log.event_type)" class="flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center mr-2">
                    <font-awesome-icon :icon="getEventTypeIcon(log.event_type)" class="text-white" />
                  </div>
                  <div>
                    <div class="text-sm font-medium text-gray-900">{{ formatEventType(log.event_type) }}</div>
                    <div class="text-sm text-gray-500">{{ formatEventName(log.event_name) }}</div>
                  </div>
                </div>
              </td>
              <td class="py-3 px-4 text-sm text-gray-900">
                {{ log.actor_id || 'System' }}
                <span v-if="log.actor_type" class="text-xs text-gray-500">({{ log.actor_type }})</span>
              </td>
              <td class="py-3 px-4 text-sm text-gray-500 max-w-md truncate">
                {{ log.description }}
              </td>
              <td class="py-3 px-4">
                <span :class="getStatusBadgeClass(log.status)">
                  {{ log.status }}
                </span>
              </td>
              <td class="py-3 px-4 text-sm">
                <button 
                  @click="viewLogDetails(log)" 
                  class="text-blue-600 hover:text-blue-800"
                >
                  <font-awesome-icon :icon="['fas', 'info-circle']" />
                  Details
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        
        <!-- Pagination -->
        <div class="flex items-center justify-between border-t border-gray-200 px-4 py-3">
          <div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
            <div>
              <p class="text-sm text-gray-700">
                Showing <span class="font-medium">{{ startItem }}</span> to <span class="font-medium">{{ endItem }}</span> of <span class="font-medium">{{ totalItems }}</span> results
              </p>
            </div>
            <div>
              <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                <button
                  @click="changePage(currentPage - 1)"
                  :disabled="currentPage === 1"
                  :class="[
                    'relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium',
                    currentPage === 1 
                      ? 'text-gray-300 cursor-not-allowed' 
                      : 'text-gray-500 hover:bg-gray-50'
                  ]"
                >
                  <span class="sr-only">Previous</span>
                  <font-awesome-icon :icon="['fas', 'chevron-left']" />
                </button>
                
                <span 
                  v-for="page in visiblePages" 
                  :key="page"
                  :class="[
                    'relative inline-flex items-center px-4 py-2 border text-sm font-medium',
                    page === currentPage
                      ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                      : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                  ]"
                  @click="page !== '...' && changePage(page)"
                >
                  {{ page }}
                </span>
                
                <button
                  @click="changePage(currentPage + 1)"
                  :disabled="currentPage === totalPages"
                  :class="[
                    'relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium',
                    currentPage === totalPages 
                      ? 'text-gray-300 cursor-not-allowed' 
                      : 'text-gray-500 hover:bg-gray-50'
                  ]"
                >
                  <span class="sr-only">Next</span>
                  <font-awesome-icon :icon="['fas', 'chevron-right']" />
                </button>
              </nav>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Log Details Modal -->
    <div v-if="selectedLog" class="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50 p-4">
      <div class="bg-white rounded-lg max-w-2xl w-full max-h-full overflow-y-auto">
        <div class="px-6 py-4 border-b flex justify-between items-center">
          <h3 class="text-lg font-medium text-gray-900">
            Audit Log Details
          </h3>
          <button @click="selectedLog = null" class="text-gray-400 hover:text-gray-500">
            <font-awesome-icon :icon="['fas', 'times']" />
          </button>
        </div>
        
        <div class="p-6">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <div class="text-sm font-medium text-gray-500">Event Type</div>
              <div class="mt-1 text-sm text-gray-900">{{ formatEventType(selectedLog.event_type) }}</div>
            </div>
            
            <div>
              <div class="text-sm font-medium text-gray-500">Event Name</div>
              <div class="mt-1 text-sm text-gray-900">{{ formatEventName(selectedLog.event_name) }}</div>
            </div>
            
            <div>
              <div class="text-sm font-medium text-gray-500">Timestamp</div>
              <div class="mt-1 text-sm text-gray-900">{{ formatDateTime(selectedLog.created_at) }}</div>
            </div>
            
            <div>
              <div class="text-sm font-medium text-gray-500">Status</div>
              <div class="mt-1">
                <span :class="getStatusBadgeClass(selectedLog.status)">
                  {{ selectedLog.status }}
                </span>
              </div>
            </div>
            
            <div>
              <div class="text-sm font-medium text-gray-500">Actor</div>
              <div class="mt-1 text-sm text-gray-900">
                {{ selectedLog.actor_id || 'System' }}
                <span v-if="selectedLog.actor_type" class="text-xs text-gray-500">({{ selectedLog.actor_type }})</span>
              </div>
            </div>
            
            <div v-if="selectedLog.target_id">
              <div class="text-sm font-medium text-gray-500">Target</div>
              <div class="mt-1 text-sm text-gray-900">
                {{ selectedLog.target_id }}
                <span v-if="selectedLog.target_type" class="text-xs text-gray-500">({{ selectedLog.target_type }})</span>
              </div>
            </div>
            
            <div v-if="selectedLog.ip_address">
              <div class="text-sm font-medium text-gray-500">IP Address</div>
              <div class="mt-1 text-sm text-gray-900">{{ selectedLog.ip_address }}</div>
            </div>
            
            <div v-if="selectedLog.session_id">
              <div class="text-sm font-medium text-gray-500">Session ID</div>
              <div class="mt-1 text-sm text-gray-900">{{ selectedLog.session_id }}</div>
            </div>
          </div>
          
          <div class="mb-4">
            <div class="text-sm font-medium text-gray-500">Description</div>
            <div class="mt-1 text-sm text-gray-900">{{ selectedLog.description }}</div>
          </div>
          
          <div v-if="selectedLog.metadata">
            <div class="text-sm font-medium text-gray-500">Additional Data</div>
            <div class="mt-1 bg-gray-50 p-3 rounded-md">
              <pre class="text-xs text-gray-900 whitespace-pre-wrap">{{ JSON.stringify(selectedLog.metadata, null, 2) }}</pre>
            </div>
          </div>
        </div>
        
        <div class="px-6 py-4 border-t bg-gray-50 flex justify-end">
          <button 
            @click="selectedLog = null" 
            class="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-md transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { default as apiClient } from '@/api/api';
import { formatDistanceToNow, format, parseISO } from 'date-fns';

export default {
  name: 'AuditLogs',
  
  data() {
    return {
      auditLogs: [],
      loading: true,
      error: null,
      selectedLog: null,
      
      // Filters
      filters: {
        eventType: '',
        eventName: '',
        actorId: '',
        status: '',
        startDate: '',
        endDate: ''
      },
      
      // Pagination
      currentPage: 1,
      pageSize: 20,
      totalItems: 0,
      totalPages: 1
    };
  },
  
  computed: {
    startItem() {
      return (this.currentPage - 1) * this.pageSize + 1;
    },
    
    endItem() {
      return Math.min(this.currentPage * this.pageSize, this.totalItems);
    },
    
    visiblePages() {
      // Calculate which page numbers to display
      let pages = [];
      const maxVisible = 5;
      
      if (this.totalPages <= maxVisible) {
        // If we have few pages, show all of them
        for (let i = 1; i <= this.totalPages; i++) {
          pages.push(i);
        }
      } else {
        // Always show first page
        pages.push(1);
        
        // Calculate start and end of visible pages around current
        let start = Math.max(2, this.currentPage - 1);
        let end = Math.min(this.totalPages - 1, this.currentPage + 1);
        
        // Adjust if we're at the beginning or end
        if (start <= 2) {
          end = start + 2;
        }
        if (end >= this.totalPages - 1) {
          start = end - 2;
        }
        
        // Add ellipsis if needed
        if (start > 2) {
          pages.push('...');
        }
        
        // Add visible page numbers
        for (let i = start; i <= end; i++) {
          pages.push(i);
        }
        
        // Add ellipsis if needed
        if (end < this.totalPages - 1) {
          pages.push('...');
        }
        
        // Always show last page
        pages.push(this.totalPages);
      }
      
      return pages;
    }
  },
  
  mounted() {
    this.fetchAuditLogs();
  },
  
  methods: {
    async fetchAuditLogs() {
      this.loading = true;
      this.error = null;
      
      try {
        // Build query parameters
        const params = {
          skip: (this.currentPage - 1) * this.pageSize,
          limit: this.pageSize
        };
        
        // Add filters if they are set
        if (this.filters.eventType) params.event_type = this.filters.eventType;
        if (this.filters.eventName) params.event_name = this.filters.eventName;
        if (this.filters.actorId) params.actor_id = this.filters.actorId;
        if (this.filters.status) params.status = this.filters.status;
        if (this.filters.startDate) params.start_date = this.filters.startDate;
        if (this.filters.endDate) params.end_date = this.filters.endDate;
        
        // Make API request
        const response = await apiClient.get('/api/audit-logs', { params });
        
        this.auditLogs = response.data.items;
        this.totalItems = response.data.total;
        this.totalPages = Math.ceil(this.totalItems / this.pageSize);
      } catch (err) {
        console.error('Error fetching audit logs:', err);
        this.error = 'Failed to load audit logs. Please try again later.';
      } finally {
        this.loading = false;
      }
    },
    
    applyFilters() {
      this.currentPage = 1; // Reset to first page
      this.fetchAuditLogs();
    },
    
    resetFilters() {
      this.filters = {
        eventType: '',
        eventName: '',
        actorId: '',
        status: '',
        startDate: '',
        endDate: ''
      };
      this.currentPage = 1;
      this.fetchAuditLogs();
    },
    
    changePage(page) {
      if (page < 1 || page > this.totalPages) return;
      this.currentPage = page;
      this.fetchAuditLogs();
    },
    
    viewLogDetails(log) {
      this.selectedLog = log;
    },
    
    formatDate(dateString) {
      try {
        const date = parseISO(dateString);
        return formatDistanceToNow(date, { addSuffix: true });
      } catch (e) {
        return dateString;
      }
    },
    
    formatDateTime(dateString) {
      try {
        const date = parseISO(dateString);
        return format(date, 'PPpp'); // Format as "Mar 15, 2025, 12:00 PM"
      } catch (e) {
        return dateString;
      }
    },
    
    formatEventType(type) {
      switch (type) {
        case 'auth': return 'Authentication';
        case 'admin': return 'Administration';
        case 'key': return 'Key Management';
        case 'data': return 'Data Access';
        default: return type;
      }
    },
    
    formatEventName(name) {
      // Convert snake_case to Title Case with spaces
      return name
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
    },
    
    getEventTypeClass(type) {
      switch (type) {
        case 'auth': return 'bg-blue-500';
        case 'admin': return 'bg-purple-500';
        case 'key': return 'bg-yellow-500';
        case 'data': return 'bg-green-500';
        default: return 'bg-gray-500';
      }
    },
    
    getEventTypeIcon(type) {
      switch (type) {
        case 'auth': return ['fas', 'user-shield'];
        case 'admin': return ['fas', 'user-cog'];
        case 'key': return ['fas', 'key'];
        case 'data': return ['fas', 'database'];
        default: return ['fas', 'clipboard-check'];
      }
    },
    
    getStatusBadgeClass(status) {
      const baseClasses = 'px-2 py-1 text-xs font-medium rounded-full';
      
      switch (status) {
        case 'success':
          return `${baseClasses} bg-green-100 text-green-800`;
        case 'failure':
          return `${baseClasses} bg-red-100 text-red-800`;
        case 'error':
          return `${baseClasses} bg-red-100 text-red-800`;
        case 'warning':
          return `${baseClasses} bg-yellow-100 text-yellow-800`;
        default:
          return `${baseClasses} bg-gray-100 text-gray-800`;
      }
    }
  }
};
</script>

<style scoped>
.audit-logs-container {
  padding: 1.5rem;
}
</style> 