<template>
  <div class="notifications-container">
    <transition-group name="notification">
      <div 
        v-for="notification in notificationStore.notifications" 
        :key="notification.id"
        :class="['notification', `notification-${notification.type}`]"
        @click="notificationStore.remove(notification.id)"
      >
        <div class="notification-content">
          {{ notification.message }}
        </div>
        <button class="notification-close" @click.stop="notificationStore.remove(notification.id)">
          &times;
        </button>
      </div>
    </transition-group>
  </div>
</template>

<script>
import { useNotificationStore } from '../stores/notification';

export default {
  name: 'NotificationsContainer',
  setup() {
    const notificationStore = useNotificationStore();
    return { notificationStore };
  }
};
</script>

<style scoped>
.notifications-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  max-width: 350px;
  width: 100%;
}

.notification {
  margin-bottom: 10px;
  padding: 15px;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  background: white;
  color: #333;
  display: flex;
  align-items: center;
  justify-content: space-between;
  animation: slide-in 0.3s ease;
  cursor: pointer;
}

.notification-content {
  flex-grow: 1;
  word-break: break-word;
}

.notification-close {
  background: transparent;
  border: none;
  font-size: 20px;
  margin-left: 10px;
  cursor: pointer;
  opacity: 0.6;
  color: inherit;
}

.notification-close:hover {
  opacity: 1;
}

.notification-error {
  background: #fee;
  color: #d33;
  border-left: 4px solid #d33;
}

.notification-success {
  background: #efe;
  color: #3c3;
  border-left: 4px solid #3c3;
}

.notification-warning {
  background: #ffd;
  color: #994;
  border-left: 4px solid #cc3;
}

.notification-info {
  background: #eef;
  color: #33c;
  border-left: 4px solid #33c;
}

/* Dark mode styles */
:root[data-theme="dark"] .notification {
  background: #333;
  color: #eee;
}

:root[data-theme="dark"] .notification-error {
  background: #422;
  border-left: 4px solid #d33;
}

:root[data-theme="dark"] .notification-success {
  background: #242;
  border-left: 4px solid #3c3;
}

:root[data-theme="dark"] .notification-warning {
  background: #442;
  border-left: 4px solid #cc3;
}

:root[data-theme="dark"] .notification-info {
  background: #224;
  border-left: 4px solid #33c;
}

/* Transitions */
.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s ease;
}

.notification-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.notification-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

@keyframes slide-in {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
</style>
