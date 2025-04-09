<template>
  <div
    aria-live="assertive"
    class="fixed inset-0 flex items-end px-4 py-6 pointer-events-none sm:p-6 sm:items-start z-50"
  >
    <div class="w-full flex flex-col items-center space-y-4 sm:items-end">
      <!-- Notification group -->
      <TransitionGroup
        name="notification"
        tag="div"
        class="max-w-sm w-full space-y-4"
      >
        <div
          v-for="notification in notifications"
          :key="notification.id"
          class="w-full bg-white shadow-lg rounded-lg pointer-events-auto ring-1 overflow-hidden"
          :class="[
            notification.type === 'success' ? 'ring-green-500' : '',
            notification.type === 'error' ? 'ring-red-500' : '',
            notification.type === 'warning' ? 'ring-yellow-500' : '',
            notification.type === 'info' ? 'ring-blue-500' : '',
          ]"
        >
          <div class="p-4">
            <div class="flex items-start">
              <!-- Icon based on notification type -->
              <div class="flex-shrink-0">
                <CheckCircleIcon v-if="notification.type === 'success'" class="h-6 w-6 text-green-500" />
                <XCircleIcon v-if="notification.type === 'error'" class="h-6 w-6 text-red-500" />
                <ExclamationTriangleIcon v-if="notification.type === 'warning'" class="h-6 w-6 text-yellow-500" />
                <InformationCircleIcon v-if="notification.type === 'info'" class="h-6 w-6 text-blue-500" />
              </div>
              
              <!-- Content -->
              <div class="ml-3 w-0 flex-1 pt-0.5">
                <p v-if="notification.title" class="text-sm font-medium text-gray-900">
                  {{ notification.title }}
                </p>
                <p class="text-sm text-gray-500">
                  {{ notification.message }}
                </p>
              </div>
              
              <!-- Close button -->
              <div class="ml-4 flex-shrink-0 flex">
                <button
                  type="button"
                  @click="dismiss(notification.id)"
                  class="bg-white rounded-md inline-flex text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  <span class="sr-only">Close</span>
                  <XMarkIcon class="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>
          
          <!-- Progress bar -->
          <div 
            v-if="notification.duration > 0"
            class="h-1 bg-gray-200"
          >
            <div 
              :class="[
                'h-full transition-all duration-100',
                notification.type === 'success' ? 'bg-green-500' : '',
                notification.type === 'error' ? 'bg-red-500' : '',
                notification.type === 'warning' ? 'bg-yellow-500' : '',
                notification.type === 'info' ? 'bg-blue-500' : '',
              ]"
              :style="{ width: `${notification.progress}%` }"
            ></div>
          </div>
        </div>
      </TransitionGroup>
    </div>
  </div>
</template>

<script setup>
import { storeToRefs } from 'pinia';
import { useNotificationStore } from '../store/notifications';
import { ref, onMounted, onUnmounted } from 'vue';
import { 
  CheckCircleIcon, 
  XCircleIcon, 
  ExclamationTriangleIcon, 
  InformationCircleIcon,
  XMarkIcon
} from '@heroicons/vue/24/solid';

const notificationStore = useNotificationStore();
const { notifications } = storeToRefs(notificationStore);

// For handling progress bars
const progressIntervals = ref({});

// Watch for new notifications and set up timers for them
onMounted(() => {
  // Set up an interval to update progress bars every 100ms
  const updateProgressInterval = setInterval(() => {
    notifications.value.forEach(notification => {
      if (notification.duration > 0) {
        const elapsedTime = Date.now() - notification.timestamp;
        const progress = 100 - (elapsedTime / notification.duration) * 100;
        
        // Update the progress
        notification.progress = Math.max(0, progress);
        
        // Auto-dismiss when progress reaches 0
        if (progress <= 0) {
          dismiss(notification.id);
        }
      }
    });
  }, 100);

  // Save reference to clear on unmounted
  progressIntervals.value.updateProgress = updateProgressInterval;
});

onUnmounted(() => {
  // Clean up all intervals
  Object.values(progressIntervals.value).forEach(interval => {
    clearInterval(interval);
  });
});

function dismiss(id) {
  notificationStore.removeNotification(id);
}
</script>

<style scoped>
.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s ease;
}

.notification-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.notification-leave-to {
  opacity: 0;
  transform: translateY(-30px);
}
</style> 