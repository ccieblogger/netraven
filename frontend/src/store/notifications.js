import { defineStore } from 'pinia';

let nextId = 1;

export const useNotificationStore = defineStore('notifications', {
  state: () => ({
    notifications: [], // Array of notification objects
  }),
  getters: {
    // Return notifications sorted by timestamp (newest first)
    sortedNotifications: (state) => {
      return [...state.notifications].sort((a, b) => b.timestamp - a.timestamp);
    }
  },
  actions: {
    /**
     * Add a notification
     * @param {Object} notification
     * @param {string} notification.title - Optional title
     * @param {string} notification.message - Message content
     * @param {string} notification.type - One of: 'info', 'success', 'warning', 'error'
     * @param {number} notification.duration - Duration in ms (0 for no auto-dismiss)
     */
    addNotification({ title = '', message, type = 'info', duration = 5000 }) {
      const id = nextId++;
      
      const newNotification = {
        id,
        title,
        message,
        type,
        duration,
        timestamp: Date.now(),
        progress: 100 // Start at 100% for progress bar
      };
      
      this.notifications.push(newNotification);
      
      // No auto-dismiss if duration is 0 or negative
      if (duration > 0) {
        // We'll use the progress tracking in the component instead of timeout
        // The component will call removeNotification when progress reaches 0
      }
      
      return id; // Return ID to allow programmatic dismissal
    },
    
    /**
     * Remove a notification by ID
     * @param {number} id - Notification ID
     */
    removeNotification(id) {
      const index = this.notifications.findIndex(n => n.id === id);
      if (index !== -1) {
        this.notifications.splice(index, 1);
      }
    },
    
    /**
     * Convenience method for info notifications
     * @param {string|Object} messageOrOptions - Message string or options object
     * @param {number} duration - Optional duration override
     */
    info(messageOrOptions, duration) {
      if (typeof messageOrOptions === 'string') {
        return this.addNotification({ 
          message: messageOrOptions, 
          type: 'info', 
          duration: duration !== undefined ? duration : 5000 
        });
      } else {
        return this.addNotification({ 
          ...messageOrOptions, 
          type: 'info' 
        });
      }
    },
    
    /**
     * Convenience method for success notifications
     * @param {string|Object} messageOrOptions - Message string or options object
     * @param {number} duration - Optional duration override
     */
    success(messageOrOptions, duration) {
      if (typeof messageOrOptions === 'string') {
        return this.addNotification({ 
          message: messageOrOptions, 
          type: 'success', 
          duration: duration !== undefined ? duration : 5000 
        });
      } else {
        return this.addNotification({ 
          ...messageOrOptions, 
          type: 'success' 
        });
      }
    },
    
    /**
     * Convenience method for warning notifications
     * @param {string|Object} messageOrOptions - Message string or options object
     * @param {number} duration - Optional duration override
     */
    warning(messageOrOptions, duration) {
      if (typeof messageOrOptions === 'string') {
        return this.addNotification({ 
          message: messageOrOptions, 
          type: 'warning', 
          duration: duration !== undefined ? duration : 7000 
        });
      } else {
        return this.addNotification({ 
          ...messageOrOptions, 
          type: 'warning' 
        });
      }
    },
    
    /**
     * Convenience method for error notifications
     * @param {string|Object} messageOrOptions - Message string or options object
     * @param {number} duration - Optional duration override (0 for persistent)
     */
    error(messageOrOptions, duration) {
      if (typeof messageOrOptions === 'string') {
        return this.addNotification({ 
          message: messageOrOptions, 
          type: 'error', 
          duration: duration !== undefined ? duration : 10000 
        });
      } else {
        return this.addNotification({ 
          ...messageOrOptions, 
          type: 'error' 
        });
      }
    },
    
    /**
     * Clear all notifications
     */
    clearAll() {
      this.notifications = [];
    }
  }
});
