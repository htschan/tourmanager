<template>
  <div class="admin-dashboard">
    <div class="admin-header">
      <h1>👥 User Management</h1>
      <div class="header-actions">
        <button @click="refreshUsers" class="btn btn-secondary" :disabled="loading">
          🔄 Refresh
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading users...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <p>❌ {{ error }}</p>
      <button @click="refreshUsers" class="btn btn-primary">
        Try Again
      </button>
    </div>

    <!-- Users Table -->
    <div v-else class="users-table-container">
      <table class="users-table">
        <thead>
          <tr>
            <th>Username</th>
            <th>Email</th>
            <th>Role</th>
            <th>Status</th>
            <th>Created</th>
            <th>Last Login</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.username">
            <td>{{ user.username }}</td>
            <td>{{ user.email }}</td>
            <td>
              <span :class="['role-badge', `role-${user.role.toLowerCase()}`]">
                {{ user.role }}
              </span>
            </td>
            <td>
              <span :class="['status-badge', `status-${user.status.toLowerCase()}`]">
                {{ user.status }}
              </span>
              <span v-if="!user.email_verified" class="email-pending-badge">
                Email Confirmation Pending
              </span>
            </td>
            <td>{{ formatDate(user.created_at) }}</td>
            <td>{{ user.last_login ? formatDate(user.last_login) : 'Never' }}</td>
            <td>
              <div class="user-actions">
                <select 
                  v-if="user.role !== 'ADMIN'"
                  v-model="user.status"
                  @change="updateStatus(user)"
                  :disabled="updating === user.username"
                >
                  <option value="PENDING">Pending</option>
                  <option value="ACTIVE">Active</option>
                  <option value="DISABLED">Disabled</option>
                </select>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useUserStore } from '../stores/users'
import { format } from 'date-fns'
import { de } from 'date-fns/locale'

const userStore = useUserStore()
const loading = ref(false)
const error = ref(null)
const updating = ref(null)

const users = ref([])

async function refreshUsers() {
  loading.value = true
  error.value = null
  try {
    await userStore.fetchUsers()
    users.value = userStore.users
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function updateStatus(user) {
  updating.value = user.username
  try {
    await userStore.updateUserStatus(user.username, user.status)
  } finally {
    updating.value = null
  }
}

function formatDate(dateString) {
  try {
    return format(new Date(dateString), 'dd.MM.yyyy HH:mm', { locale: de })
  } catch {
    return dateString
  }
}

onMounted(refreshUsers)
</script>

<style scoped>
.admin-dashboard {
  padding: 2rem;
}

.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.header-actions {
  display: flex;
  gap: 1rem;
}

.loading-state,
.error-state {
  text-align: center;
  padding: 3rem;
  color: #7f8c8d;
}

.users-table-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow: auto;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.users-table th,
.users-table td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.users-table th {
  background: #f8f9fa;
  font-weight: 600;
  color: #2c3e50;
}

.email-pending-badge {
  display: block;
  margin-top: 0.5rem;
  font-size: 0.75rem;
  padding: 0.2rem 0.5rem;
  background-color: #fff3cd;
  color: #856404;
  border: 1px solid #ffeeba;
  border-radius: 4px;
  font-weight: 500;
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

.user-actions {
  display: flex;
  gap: 0.5rem;
}

select {
  padding: 0.25rem 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
  background: white;
}

select:disabled {
  background: #f8f9fa;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .admin-dashboard {
    padding: 1rem;
  }

  .admin-header {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }

  .users-table th,
  .users-table td {
    padding: 0.75rem;
  }
}
</style>
