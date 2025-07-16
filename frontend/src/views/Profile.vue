<template>
  <div class="profile-view">
    <h1>Profile</h1>
    
    <div class="profile-content">
      <!-- User Info Section -->
      <div class="user-info card mb-4">
        <div class="card-body">
          <h3>User Information</h3>
          <div class="info-row">
            <strong>Username:</strong>
            <span>{{ user?.username }}</span>
          </div>
          <div class="info-row">
            <strong>Email:</strong>
            <span>{{ user?.email }}</span>
          </div>
          <div class="info-row">
            <strong>Role:</strong>
            <span>{{ user?.role }}</span>
          </div>
          <div class="info-row">
            <strong>Status:</strong>
            <span>{{ user?.status }}</span>
          </div>
          <div class="info-row">
            <strong>Member Since:</strong>
            <span>{{ formatDate(user?.created_at) }}</span>
          </div>
          <div class="info-row">
            <strong>Last Login:</strong>
            <span>{{ formatDate(user?.last_login) || 'Never' }}</span>
          </div>
        </div>
      </div>
      
      <!-- Password Change Section -->
      <div class="password-section card">
        <div class="card-body">
          <PasswordChangeForm />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import PasswordChangeForm from '../components/PasswordChangeForm.vue'
import { format } from 'date-fns'
import { de } from 'date-fns/locale'

const authStore = useAuthStore()
const user = authStore.getUser

function formatDate(date) {
  if (!date) return null
  return format(new Date(date), 'PPP', { locale: de })
}

onMounted(async () => {
  if (!user) {
    await authStore.fetchUser()
  }
})
</script>

<style scoped>
.profile-view {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.profile-content {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
}

@media (min-width: 768px) {
  .profile-content {
    grid-template-columns: 1fr 1fr;
  }
}

.card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #eee;
}

.info-row:last-child {
  border-bottom: none;
}

h1 {
  margin-bottom: 30px;
}

h3 {
  margin-bottom: 20px;
  color: #333;
}
</style>
