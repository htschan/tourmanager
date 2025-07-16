<template>
  <div class="password-change-form">
    <h2>Change Password</h2>
    
    <div v-if="message" :class="['alert', success ? 'alert-success' : 'alert-danger']">
      {{ message }}
    </div>
    
    <form @submit.prevent="handleSubmit" class="mt-4">
      <div class="form-group mb-3">
        <label for="currentPassword">Current Password</label>
        <input
          type="password"
          id="currentPassword"
          v-model="form.currentPassword"
          class="form-control"
          required
          :disabled="loading"
        />
      </div>
      
      <div class="form-group mb-3">
        <label for="newPassword">New Password</label>
        <input
          type="password"
          id="newPassword"
          v-model="form.newPassword"
          class="form-control"
          required
          :disabled="loading"
          minlength="8"
        />
      </div>
      
      <div class="form-group mb-3">
        <label for="confirmPassword">Confirm New Password</label>
        <input
          type="password"
          id="confirmPassword"
          v-model="form.confirmPassword"
          class="form-control"
          required
          :disabled="loading"
        />
        <div v-if="!passwordsMatch" class="text-danger mt-1">
          Passwords do not match
        </div>
      </div>
      
      <button 
        type="submit" 
        class="btn btn-primary"
        :disabled="loading || !isValid"
      >
        <span v-if="loading" class="spinner-border spinner-border-sm me-2" role="status"></span>
        Change Password
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast'

const authStore = useAuthStore()
const toastStore = useToastStore()

const form = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const loading = ref(false)
const message = ref('')
const success = ref(false)

const passwordsMatch = computed(() => 
  !form.value.confirmPassword || form.value.newPassword === form.value.confirmPassword
)

const isValid = computed(() => 
  form.value.currentPassword && 
  form.value.newPassword && 
  form.value.confirmPassword && 
  passwordsMatch.value &&
  form.value.newPassword.length >= 8
)

async function handleSubmit() {
  if (!isValid.value) return
  
  loading.value = true
  message.value = ''
  
  try {
    const result = await authStore.changePassword(
      form.value.currentPassword,
      form.value.newPassword
    )
    
    if (result.success) {
      success.value = true
      message.value = result.message
      toastStore.show({
        message: 'Password changed successfully',
        type: 'success'
      })
      // Reset form
      form.value = {
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      }
    } else {
      success.value = false
      message.value = result.message
      toastStore.show({
        message: result.message,
        type: 'error'
      })
    }
  } catch (error) {
    success.value = false
    message.value = 'An error occurred while changing password'
    toastStore.show({
      message: 'Failed to change password',
      type: 'error'
    })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.password-change-form {
  max-width: 400px;
  margin: 0 auto;
  padding: 20px;
}

.alert {
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 15px;
}

.alert-success {
  background-color: #d4edda;
  border-color: #c3e6cb;
  color: #155724;
}

.alert-danger {
  background-color: #f8d7da;
  border-color: #f5c6cb;
  color: #721c24;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
}

.form-control {
  width: 100%;
  padding: 8px;
  border: 1px solid #ced4da;
  border-radius: 4px;
}

.btn-primary {
  background-color: #007bff;
  border-color: #007bff;
  color: white;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.btn-primary:disabled {
  background-color: #6c757d;
  border-color: #6c757d;
  cursor: not-allowed;
}
</style>
