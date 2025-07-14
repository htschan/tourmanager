<template>
  <div class="admin-container">
    <h1>User Administration</h1>
    
    <div class="pending-users" v-if="pendingUsers.length > 0">
      <h2>Pending Approvals</h2>
      <div class="user-list">
        <div v-for="user in pendingUsers" :key="user.username" class="user-card">
          <div class="user-info">
            <h3>{{ user.username }}</h3>
            <p>{{ user.email }}</p>
            <p>Registered: {{ new Date(user.created_at).toLocaleDateString() }}</p>
          </div>
          <div class="user-actions">
            <button 
              class="approve-btn"
              @click="updateUserStatus(user.username, 'active')"
              :disabled="loading"
            >
              Approve
            </button>
            <button 
              class="reject-btn"
              @click="updateUserStatus(user.username, 'disabled')"
              :disabled="loading"
            >
              Reject
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <div class="all-users">
      <h2>All Users</h2>
      <div class="user-list">
        <div v-for="user in allUsers" :key="user.username" class="user-card">
          <div class="user-info">
            <h3>{{ user.username }}</h3>
            <p>{{ user.email }}</p>
            <p>Status: {{ user.status }}</p>
            <p>Role: {{ user.role }}</p>
            <p>Last Login: {{ user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never' }}</p>
          </div>
          <div class="user-actions">
            <button 
              v-if="user.status !== 'active'"
              class="approve-btn"
              @click="updateUserStatus(user.username, 'active')"
              :disabled="loading"
            >
              Activate
            </button>
            <button 
              v-if="user.status !== 'disabled'"
              class="reject-btn"
              @click="updateUserStatus(user.username, 'disabled')"
              :disabled="loading"
            >
              Disable
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from '../stores/users'
import { useToastStore } from '../stores/toast'

const userStore = useUserStore()
const toastStore = useToastStore()
const loading = ref(false)
const allUsers = ref([])
const pendingUsers = ref([])

const fetchUsers = async () => {
  try {
    loading.value = true
    const users = await userStore.fetchUsers()
    allUsers.value = users
    pendingUsers.value = users.filter(user => user.status === 'pending')
  } catch (error) {
    toastStore.showError('Failed to load users')
  } finally {
    loading.value = false
  }
}

const updateUserStatus = async (username, status) => {
  try {
    loading.value = true
    await userStore.updateUserStatus(username, status)
    await fetchUsers() // Refresh the lists
    toastStore.showSuccess(`User ${username} has been ${status}`)
  } catch (error) {
    toastStore.showError('Failed to update user status')
  } finally {
    loading.value = false
  }
}

onMounted(fetchUsers)
</script>

<style scoped>
.admin-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

h1 {
  margin-bottom: 30px;
  color: #2c3e50;
}

h2 {
  margin: 20px 0;
  color: #34495e;
}

.user-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.user-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.user-info h3 {
  margin: 0 0 10px 0;
  color: #2c3e50;
}

.user-info p {
  margin: 5px 0;
  color: #666;
}

.user-actions {
  display: flex;
  gap: 10px;
  margin-top: auto;
}

button {
  padding: 8px 16px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.approve-btn {
  background-color: #42b983;
  color: white;
}

.approve-btn:hover:not(:disabled) {
  background-color: #3aa876;
}

.reject-btn {
  background-color: #e74c3c;
  color: white;
}

.reject-btn:hover:not(:disabled) {
  background-color: #d44133;
}

.pending-users {
  background-color: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
}
</style>
