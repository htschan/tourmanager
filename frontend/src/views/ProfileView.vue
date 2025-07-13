<template>
  <div class="profile-container">
    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading profile...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <p>❌ {{ error }}</p>
      <button @click="loadProfile" class="btn btn-primary">
        Try Again
      </button>
    </div>

    <!-- Profile Content -->
    <div v-else-if="profile" class="profile-content">
      <div class="profile-header">
        <h1>👤 My Profile</h1>
      </div>

      <div class="profile-card">
        <div class="profile-section">
          <div class="profile-field">
            <label>Username</label>
            <div class="field-value">{{ profile.username }}</div>
          </div>

          <div class="profile-field">
            <label>Email</label>
            <div class="field-value">{{ profile.email }}</div>
          </div>

          <div class="profile-field">
            <label>Role</label>
            <div class="field-value">
              <span :class="['role-badge', `role-${profile.role.toLowerCase()}`]">
                {{ profile.role }}
              </span>
            </div>
          </div>

          <div class="profile-field">
            <label>Status</label>
            <div class="field-value">
              <span :class="['status-badge', `status-${profile.status.toLowerCase()}`]">
                {{ profile.status }}
              </span>
            </div>
          </div>

          <div class="profile-field">
            <label>Account Created</label>
            <div class="field-value">{{ formatDate(profile.created_at) }}</div>
          </div>

          <div class="profile-field">
            <label>Last Login</label>
            <div class="field-value">
              {{ profile.last_login ? formatDate(profile.last_login) : 'Never' }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from '../stores/users'
import { format } from 'date-fns'
import { de } from 'date-fns/locale'

const userStore = useUserStore()
const loading = ref(false)
const error = ref(null)
const profile = ref(null)

async function loadProfile() {
  loading.value = true
  error.value = null
  try {
    profile.value = await userStore.fetchProfile()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function formatDate(dateString) {
  try {
    return format(new Date(dateString), 'dd.MM.yyyy HH:mm', { locale: de })
  } catch {
    return dateString
  }
}

onMounted(loadProfile)
</script>

<style scoped>
.profile-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}

.profile-header {
  margin-bottom: 2rem;
}

.profile-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  padding: 2rem;
}

.profile-section {
  display: grid;
  gap: 1.5rem;
}

.profile-field {
  display: grid;
  gap: 0.5rem;
}

.profile-field label {
  font-size: 0.9rem;
  color: #7f8c8d;
  font-weight: 500;
}

.field-value {
  font-size: 1.1rem;
  color: #2c3e50;
}

.loading-state,
.error-state {
  text-align: center;
  padding: 3rem;
  color: #7f8c8d;
}

.role-badge,
.status-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
}

.role-admin {
  background: #8e44ad;
  color: white;
}

.role-user {
  background: #3498db;
  color: white;
}

.status-active {
  background: #27ae60;
  color: white;
}

.status-pending {
  background: #f39c12;
  color: white;
}

.status-disabled {
  background: #e74c3c;
  color: white;
}

@media (max-width: 768px) {
  .profile-container {
    padding: 1rem;
  }

  .profile-card {
    padding: 1.5rem;
  }
}
</style>
