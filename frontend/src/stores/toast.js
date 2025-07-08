import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useToastStore = defineStore('toast', () => {
  const toasts = ref([])
  let nextId = 1

  const addToast = (message, type = 'info', duration = 5000) => {
    const id = nextId++
    const toast = {
      id,
      message,
      type,
      duration
    }
    
    toasts.value.push(toast)
    
    // Auto-remove toast after duration
    if (duration > 0) {
      setTimeout(() => {
        removeToast(id)
      }, duration)
    }
    
    return id
  }

  const removeToast = (id) => {
    const index = toasts.value.findIndex(toast => toast.id === id)
    if (index > -1) {
      toasts.value.splice(index, 1)
    }
  }

  const clearAllToasts = () => {
    toasts.value = []
  }

  // Convenience methods
  const success = (message, duration = 5000) => {
    return addToast(message, 'success', duration)
  }

  const error = (message, duration = 8000) => {
    return addToast(message, 'error', duration)
  }

  const info = (message, duration = 5000) => {
    return addToast(message, 'info', duration)
  }

  const warning = (message, duration = 6000) => {
    return addToast(message, 'warning', duration)
  }

  return {
    toasts,
    addToast,
    removeToast,
    clearAllToasts,
    success,
    error,
    info,
    warning
  }
})
