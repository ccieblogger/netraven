<template>
  <div class="p-8 bg-white max-w-lg mx-auto mt-8 rounded shadow">
    <h1 class="text-2xl font-bold mb-4">Route Test Page</h1>
    <p class="mb-4">This is a simple test page to verify routing works correctly.</p>
    
    <div class="bg-blue-100 p-4 rounded mb-4">
      <h2 class="font-bold mb-2">Current Route:</h2>
      <pre class="text-xs">{{ currentRoute }}</pre>
    </div>
    
    <div class="space-y-2">
      <button @click="goToDashboard" class="w-full bg-blue-600 text-white px-4 py-2 rounded">
        Go to Dashboard
      </button>
      <button @click="goToLogin" class="w-full bg-green-600 text-white px-4 py-2 rounded">
        Go to Login
      </button>
      <button @click="testLocalStorage" class="w-full bg-purple-600 text-white px-4 py-2 rounded">
        Test localStorage
      </button>
    </div>
    
    <div v-if="testResult" class="mt-4 p-3 bg-yellow-100 rounded">
      <h3 class="font-bold">Test Result:</h3>
      <p>{{ testResult }}</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'RouteTest',
  
  data() {
    return {
      testResult: null
    }
  },
  
  computed: {
    currentRoute() {
      return {
        href: window.location.href,
        pathname: window.location.pathname,
        search: window.location.search,
        hash: window.location.hash
      }
    }
  },
  
  methods: {
    goToDashboard() {
      this.testResult = 'Navigating to Dashboard...'
      window.location.href = '/'
    },
    
    goToLogin() {
      this.testResult = 'Navigating to Login...'
      window.location.href = '/login'
    },
    
    testLocalStorage() {
      try {
        const testKey = 'route_test_' + Date.now()
        const testValue = 'Test value at ' + new Date().toISOString()
        
        // Write to localStorage
        localStorage.setItem(testKey, testValue)
        
        // Read from localStorage
        const readValue = localStorage.getItem(testKey)
        
        // Verify value
        if (readValue === testValue) {
          this.testResult = 'localStorage test passed! Value written and read successfully.'
        } else {
          this.testResult = `localStorage test failed! Written "${testValue}" but read "${readValue}"`
        }
        
        // Clean up
        localStorage.removeItem(testKey)
      } catch (error) {
        this.testResult = `localStorage test error: ${error.message}`
      }
    }
  }
}
</script> 