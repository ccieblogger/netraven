<template>
  <div class="flex h-screen bg-gray-100">
    <!-- Sidebar Navigation -->
    <nav class="bg-gray-800 text-white w-64 flex-shrink-0 hidden md:block">
      <div class="p-4">
        <h1 class="text-xl font-semibold">NetRaven</h1>
      </div>
      <div class="py-4">
        <router-link 
          to="/" 
          class="block px-4 py-2 hover:bg-gray-700"
          :class="{ 'bg-gray-700': $route.path === '/' }"
        >
          Dashboard
        </router-link>
        <router-link 
          to="/devices" 
          class="block px-4 py-2 hover:bg-gray-700"
          :class="{ 'bg-gray-700': $route.path.startsWith('/devices') }"
        >
          Devices
        </router-link>
        <router-link 
          to="/backups" 
          class="block px-4 py-2 hover:bg-gray-700"
          :class="{ 'bg-gray-700': $route.path.startsWith('/backups') }"
        >
          Backups
        </router-link>
        <router-link 
          to="/scheduled-jobs" 
          class="block px-4 py-2 hover:bg-gray-700"
          :class="{ 'bg-gray-700': $route.path.startsWith('/scheduled-jobs') }"
        >
          Scheduled Jobs
        </router-link>
        <router-link 
          to="/job-logs" 
          class="block px-4 py-2 hover:bg-gray-700"
          :class="{ 'bg-gray-700': $route.path.startsWith('/job-logs') }"
        >
          Job Logs
        </router-link>
        <router-link 
          to="/tags" 
          class="block px-4 py-2 hover:bg-gray-700"
          :class="{ 'bg-gray-700': $route.path.startsWith('/tags') }"
        >
          Tags
        </router-link>
        <router-link 
          to="/tag-rules" 
          class="block px-4 py-2 hover:bg-gray-700"
          :class="{ 'bg-gray-700': $route.path.startsWith('/tag-rules') }"
        >
          Tag Rules
        </router-link>
        <router-link 
          to="/gateway" 
          class="block px-4 py-2 hover:bg-gray-700"
          :class="{ 'bg-gray-700': $route.path.startsWith('/gateway') }"
        >
          Gateway
        </router-link>
      </div>
    </nav>
    
    <!-- Main Content -->
    <div class="flex-1 overflow-auto">
      <div class="container mx-auto p-6">
        <slot></slot>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'MainLayout'
}
</script> 