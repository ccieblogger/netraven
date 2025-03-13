<template>
  <div class="bg-white rounded-lg shadow-sm overflow-hidden">
    <div class="overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th v-for="column in columns" 
                :key="column.key"
                @click="sort(column.key)"
                class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
                :class="{ 'text-blue-600': sortKey === column.key }">
              <div class="flex items-center space-x-1">
                <span>{{ column.label }}</span>
                <span v-if="sortKey === column.key" class="text-blue-600">
                  {{ sortOrder === 'asc' ? '↑' : '↓' }}
                </span>
              </div>
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="item in sortedData" 
              :key="item.id"
              class="hover:bg-gray-50 transition-colors duration-150">
            <td v-for="column in columns" 
                :key="column.key"
                class="px-6 py-4 whitespace-nowrap text-sm relative"
                :class="column.class">
              <div class="relative z-10">
                <slot :name="column.key" :item="item">
                  {{ item[column.key] }}
                </slot>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'

export default {
  name: 'DataTable',
  
  props: {
    columns: {
      type: Array,
      required: true
    },
    data: {
      type: Array,
      required: true
    },
    defaultSort: {
      type: String,
      default: ''
    },
    defaultOrder: {
      type: String,
      default: 'desc'
    }
  },
  
  setup(props) {
    const sortKey = ref(props.defaultSort)
    const sortOrder = ref(props.defaultOrder)
    
    const sort = (key) => {
      if (sortKey.value === key) {
        sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
      } else {
        sortKey.value = key
        sortOrder.value = 'asc'
      }
    }
    
    const sortedData = computed(() => {
      if (!sortKey.value) return props.data
      
      return [...props.data].sort((a, b) => {
        const aVal = a[sortKey.value]
        const bVal = b[sortKey.value]
        
        if (aVal === bVal) return 0
        
        const modifier = sortOrder.value === 'asc' ? 1 : -1
        
        if (typeof aVal === 'string') {
          return aVal.localeCompare(bVal) * modifier
        }
        
        return aVal > bVal ? modifier : -modifier
      })
    })
    
    return {
      sortKey,
      sortOrder,
      sort,
      sortedData
    }
  }
}
</script>

<style scoped>
.table-container {
  max-height: 400px;
  overflow-y: auto;
}

/* Custom scrollbar styling */
.table-container::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.table-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.table-container::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.table-container::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* Make table cells more clickable */
td {
  position: relative;
}

td a {
  position: relative;
  z-index: 2;
  display: inline-block;
  padding: 0.5rem 0;
}
</style> 