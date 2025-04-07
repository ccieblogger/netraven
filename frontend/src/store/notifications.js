import { defineStore } from 'pinia';

let nextId = 1;

export const useNotificationStore = defineStore('notifications', {
  state: () => ({
    messages: [], // Array of notification objects { id, text, type, timeoutId }
  }),
  actions: {
    addMessage({ text, type = 'info', duration = 5000 }) {
      const id = nextId++;
      this.messages.push({ id, text, type });

      // Automatically remove the message after the duration
      const timeoutId = setTimeout(() => {
        this.removeMessage(id);
      }, duration);

      // Store timeoutId to allow manual removal before timeout if needed
      const messageIndex = this.messages.findIndex(m => m.id === id);
      if (messageIndex !== -1) {
          this.messages[messageIndex].timeoutId = timeoutId;
      }
    },
    removeMessage(id) {
      const index = this.messages.findIndex(m => m.id === id);
      if (index !== -1) {
        // Clear the timeout if it exists before removing the message
        if (this.messages[index].timeoutId) {
            clearTimeout(this.messages[index].timeoutId);
        }
        this.messages.splice(index, 1);
      }
    },
    // Convenience methods for different notification types
    info(text, duration) {
      this.addMessage({ text, type: 'info', duration });
    },
    success(text, duration) {
      this.addMessage({ text, type: 'success', duration });
    },
    warning(text, duration) {
      this.addMessage({ text, type: 'warning', duration });
    },
    error(text, duration = 10000) { // Longer default for errors
      this.addMessage({ text, type: 'error', duration });
    },
    clearMessages() {
        // Clear all timeouts before clearing messages
        this.messages.forEach(m => {
            if (m.timeoutId) {
                clearTimeout(m.timeoutId);
            }
        });
      this.messages = [];
    }
  }
});
