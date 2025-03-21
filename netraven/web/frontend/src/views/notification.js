import { defineStore } from 'pinia';
import { v4 as uuidv4 } from 'uuid';

export const useNotificationStore = defineStore('notification', {
  state: () => ({
    notifications: []
  }),

  actions: {
    /**
     * Add a notification to the store
     * 
     * @param {Object} notification 
     * @param {string} notification.type - 'success', 'info', 'warning', 'danger'
     * @param {string} notification.title - Title of the notification
     * @param {string} notification.message - Notification message
     * @param {number} notification.timeout - Auto-dismiss after milliseconds (0 for no auto-dismiss)
     */
    addNotification({ type = 'info', title = '', message = '', timeout = 5000 }) {
      const id = uuidv4();
      
      // Add the notification
      this.notifications.push({
        id,
        type,
        title,
        message,
        timestamp: new Date(),
        dismiss: false
      });
      
      // Set up auto-dismiss if timeout is provided
      if (timeout > 0) {
        setTimeout(() => {
          this.dismissNotification(id);
        }, timeout);
      }
      
      return id;
    },
    
    /**
     * Dismiss a notification by ID
     * 
     * @param {string} id - ID of the notification to dismiss
     */
    dismissNotification(id) {
      const notificationIndex = this.notifications.findIndex(n => n.id === id);
      
      if (notificationIndex >= 0) {
        // Set dismiss flag to allow transition effects
        this.notifications[notificationIndex].dismiss = true;
        
        // Remove after animation
        setTimeout(() => {
          this.notifications = this.notifications.filter(n => n.id !== id);
        }, 300);
      }
    },
    
    /**
     * Clear all notifications
     */
    clearAll() {
      this.notifications = [];
    },
    
    /**
     * Add a success notification
     * 
     * @param {string} message 
     * @param {string} title 
     * @param {number} timeout 
     */
    success(message, title = 'Success', timeout = 5000) {
      return this.addNotification({
        type: 'success',
        title,
        message,
        timeout
      });
    },
    
    /**
     * Add an error notification
     * 
     * @param {string} message 
     * @param {string} title 
     * @param {number} timeout 
     */
    error(message, title = 'Error', timeout = 0) {
      return this.addNotification({
        type: 'danger',
        title,
        message,
        timeout
      });
    },
    
    /**
     * Add a warning notification
     * 
     * @param {string} message 
     * @param {string} title 
     * @param {number} timeout 
     */
    warning(message, title = 'Warning', timeout = 7000) {
      return this.addNotification({
        type: 'warning',
        title,
        message,
        timeout
      });
    },
    
    /**
     * Add an info notification
     * 
     * @param {string} message 
     * @param {string} title 
     * @param {number} timeout 
     */
    info(message, title = 'Information', timeout = 5000) {
      return this.addNotification({
        type: 'info',
        title,
        message,
        timeout
      });
    }
  }
}); 