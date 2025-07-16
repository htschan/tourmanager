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
              @click="updateUserStatus(user.username, UserStatus.ACTIVE)"
              :disabled="loading"
            >
              Approve
            </button>
            <button 
              class="reject-btn"
              @click="updateUserStatus(user.username, UserStatus.DISABLED)"
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
              v-if="user.status !== UserStatus.ACTIVE"
              class="approve-btn"
              @click="updateUserStatus(user.username, UserStatus.ACTIVE)"
              :disabled="loading"
            >
              Activate
            </button>
            <button 
              v-if="user.status !== UserStatus.DISABLED"
              class="reject-btn"
              @click="updateUserStatus(user.username, UserStatus.DISABLED)"
              :disabled="loading"
            >
              Disable
            </button>
            <button 
              class="delete-btn"
              @click="confirmDelete(user)"
              :disabled="loading || (authStore.getUser?.username === user.username)"
              :title="authStore.getUser?.username === user.username ? 'Cannot delete your own account' : ''"
            >
              Delete
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
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast'
import { UserStatus } from '../constants'

const userStore = useUserStore()
const authStore = useAuthStore()
const toastStore = useToastStore()
console.log('📝 Stores initialized:', { 
  userStore: !!userStore, 
  toastStore: !!toastStore,
  toastMethods: Object.keys(toastStore)
})
const loading = ref(false)
const allUsers = ref([])
const pendingUsers = ref([])

const fetchUsers = async () => {
  try {
    console.log('📝 Fetching users...')
    loading.value = true
    const users = await userStore.fetchUsers() || []
    console.log('📝 Users fetched:', users)
    allUsers.value = users
    pendingUsers.value = users?.filter(user => user.status === UserStatus.PENDING) || []
    console.log('📝 Pending users:', pendingUsers.value)
  } catch (error) {
    console.error('❌ Failed to fetch users:', error)
    toastStore.error('Failed to load users')
    allUsers.value = []
    pendingUsers.value = []
  } finally {
    loading.value = false
  }
}

const updateUserStatus = async (username, status) => {
  try {
    console.log(`📝 Updating user status - Username: ${username}, New Status: ${status}`)
    loading.value = true
    await userStore.updateUserStatus(username, status)
    console.log('✅ User status updated successfully')
    await fetchUsers() // Refresh the lists
    console.log('📝 Showing success toast notification')
    toastStore.success(`User ${username} has been ${status}`)
  } catch (error) {
    console.error('❌ Failed to update user status:', error)
    toastStore.error('Failed to update user status')
  } finally {
    loading.value = false
    console.log('📝 Update user status operation completed')
  }
}

const confirmDelete = async (user) => {
  // Check if user is trying to delete themselves
  const currentUser = authStore.getUser
  if (currentUser && currentUser.username === user.username) {
    toastStore.error('Cannot delete your own admin account')
    return
  }

  if (confirm(`Are you sure you want to delete user ${user.username}? This action cannot be undone.`)) {
    try {
      console.log(`📝 Deleting user: ${user.username}`)
      loading.value = true
      await userStore.deleteUser(user.username)
      await fetchUsers() // Refresh the lists
      toastStore.success(`User ${user.username} has been deleted`)
    } catch (error) {
      console.error('❌ Failed to delete user:', error)
      toastStore.error(error.response?.data?.detail || 'Failed to delete user')
    } finally {
      loading.value = false
      console.log('📝 Delete user operation completed')
    }
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

.delete-btn {
  background-color: #6c757d;
  color: white;
}

.delete-btn:hover:not(:disabled) {
  background-color: #5a6268;
}

.delete-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pending-users {
  background-color: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
}
</style>
