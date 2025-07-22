import { defineStore } from 'pinia';

export const useNotificationStore = defineStore('notification', {
  state: () => ({
    notifications: [],
    nextId: 0
  }),
  
  actions: {
    add(message, type = 'info', timeout = 5000) {
      const id = this.nextId++;
      
      // Add notification
      this.notifications.push({
        id,
        message,
        type, // 'info', 'success', 'warning', 'error'
        timestamp: new Date()
      });
      
      // Auto-remove after timeout if timeout > 0
      if (timeout > 0) {
        setTimeout(() => this.remove(id), timeout);
      }
      
      return id;
    },
    
    remove(id) {
      const index = this.notifications.findIndex(n => n.id === id);
      if (index !== -1) {
        this.notifications.splice(index, 1);
      }
    },
    
    // Helper methods for different notification types
    success(message, timeout = 5000) {
      return this.add(message, 'success', timeout);
    },
    
    error(message, timeout = 8000) {
      return this.add(message, 'error', timeout);
    },
    
    warning(message, timeout = 7000) {
      return this.add(message, 'warning', timeout);
    },
    
    info(message, timeout = 5000) {
      return this.add(message, 'info', timeout);
    },
    
    clearAll() {
      this.notifications = [];
    }
  }
});
