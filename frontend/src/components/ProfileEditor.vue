<template>
  <div class="profile-editor">
    <form @submit.prevent="saveProfile" class="profile-form">
      <h2>Edit Profile</h2>

      <!-- Avatar Upload -->
      <div class="avatar-section">
        <div class="current-avatar">
          <img 
            :src="formData.avatar_url || '/default-avatar.png'" 
            alt="Profile Avatar"
            class="avatar-image"
          />
        </div>
        <div class="avatar-upload">
          <label for="avatar" class="btn btn-outline">
            📷 Change Avatar
          </label>
          <input 
            type="file" 
            id="avatar" 
            accept="image/*"
            @change="handleAvatarChange" 
            class="hidden"
          />
        </div>
      </div>

      <!-- Profile Fields -->
      <div class="form-group">
        <label for="fullName">Full Name</label>
        <input
          id="fullName"
          v-model="formData.full_name"
          type="text"
          placeholder="Enter your full name"
        />
      </div>

      <div class="form-group">
        <label for="email">Email</label>
        <div class="email-field">
          <input
            id="email"
            v-model="formData.email"
            type="email"
            :disabled="!formData.email_verified"
          />
          <span 
            :class="['verification-badge', formData.email_verified ? 'verified' : 'unverified']"
          >
            {{ formData.email_verified ? '✓ Verified' : '! Unverified' }}
          </span>
        </div>
        <button 
          v-if="!formData.email_verified" 
          @click.prevent="requestVerification"
          type="button"
          class="btn btn-outline btn-sm"
        >
          Request Verification
        </button>
      </div>

      <div class="form-group">
        <label for="bio">Bio</label>
        <textarea
          id="bio"
          v-model="formData.bio"
          rows="4"
          placeholder="Tell us about yourself"
        ></textarea>
      </div>

      <!-- Preferences -->
      <div class="form-group">
        <label>Preferences</label>
        <div class="preferences-grid">
          <div class="preference-item">
            <label>
              <input 
                type="checkbox" 
                v-model="formData.preferences.emailNotifications"
              />
              Email Notifications
            </label>
          </div>
          <div class="preference-item">
            <label>
              <input 
                type="checkbox" 
                v-model="formData.preferences.darkMode"
              />
              Dark Mode
            </label>
          </div>
        </div>
      </div>

      <!-- Change Password -->
      <div class="form-group">
        <button 
          type="button" 
          @click="showPasswordChange = !showPasswordChange"
          class="btn btn-outline"
        >
          🔑 Change Password
        </button>
      </div>

      <div v-if="showPasswordChange" class="password-change">
        <div class="form-group">
          <label for="currentPassword">Current Password</label>
          <input
            id="currentPassword"
            v-model="passwordData.current"
            type="password"
            required
          />
        </div>

        <div class="form-group">
          <label for="newPassword">New Password</label>
          <input
            id="newPassword"
            v-model="passwordData.new"
            type="password"
            required
          />
        </div>

        <div class="form-group">
          <label for="confirmPassword">Confirm New Password</label>
          <input
            id="confirmPassword"
            v-model="passwordData.confirm"
            type="password"
            required
          />
        </div>
      </div>

      <div v-if="error" class="error-message">
        {{ error }}
      </div>

      <!-- Submit Buttons -->
      <div class="form-actions">
        <button 
          type="button" 
          @click="resetForm" 
          class="btn btn-secondary"
          :disabled="loading"
        >
          Cancel
        </button>
        <button 
          type="submit" 
          class="btn btn-primary"
          :disabled="loading"
        >
          {{ loading ? 'Saving...' : 'Save Changes' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from '../stores/users'
import { useToastStore } from '../stores/toast'

const userStore = useUserStore()
const toastStore = useToastStore()

const loading = ref(false)
const error = ref('')
const showPasswordChange = ref(false)

const formData = ref({
  full_name: '',
  email: '',
  bio: '',
  avatar_url: '',
  email_verified: false,
  preferences: {
    emailNotifications: true,
    darkMode: false
  }
})

const passwordData = ref({
  current: '',
  new: '',
  confirm: ''
})

const originalData = ref(null)

async function loadProfile() {
  loading.value = true
  try {
    const profile = await userStore.fetchProfile()
    formData.value = {
      ...profile,
      preferences: profile.preferences || {
        emailNotifications: true,
        darkMode: false
      }
    }
    originalData.value = JSON.parse(JSON.stringify(formData.value))
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function saveProfile() {
  if (showPasswordChange.value) {
    if (passwordData.value.new !== passwordData.value.confirm) {
      error.value = 'New passwords do not match'
      return
    }
  }

  loading.value = true
  error.value = ''

  try {
    await userStore.updateProfile({
      ...formData.value,
      ...(showPasswordChange.value ? {
        current_password: passwordData.value.current,
        new_password: passwordData.value.new
      } : {})
    })
    
    toastStore.showSuccess('Profile updated successfully')
    showPasswordChange.value = false
    passwordData.value = { current: '', new: '', confirm: '' }
    originalData.value = JSON.parse(JSON.stringify(formData.value))
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function requestVerification() {
  loading.value = true
  try {
    await userStore.requestEmailVerification(formData.value.email)
    toastStore.showSuccess('Verification email sent')
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function resetForm() {
  formData.value = JSON.parse(JSON.stringify(originalData.value))
  showPasswordChange.value = false
  passwordData.value = { current: '', new: '', confirm: '' }
  error.value = ''
}

async function handleAvatarChange(event) {
  const file = event.target.files[0]
  if (!file) return

  const formData = new FormData()
  formData.append('avatar', file)

  loading.value = true
  try {
    const response = await userStore.uploadAvatar(formData)
    formData.value.avatar_url = response.url
    toastStore.showSuccess('Avatar uploaded successfully')
  } catch (err) {
    error.value = 'Failed to upload avatar'
  } finally {
    loading.value = false
  }
}

onMounted(loadProfile)
</script>

<style scoped>
.profile-editor {
  max-width: 600px;
  margin: 0 auto;
  padding: 2rem;
}

.profile-form {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.avatar-section {
  display: flex;
  align-items: center;
  gap: 2rem;
  margin-bottom: 2rem;
}

.current-avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.hidden {
  display: none;
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #2c3e50;
}

input,
textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

input:focus,
textarea:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.1);
}

input:disabled {
  background: #f8f9fa;
  cursor: not-allowed;
}

.email-field {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.verification-badge {
  font-size: 0.8rem;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-weight: 500;
}

.verified {
  background: #27ae60;
  color: white;
}

.unverified {
  background: #f39c12;
  color: white;
}

.preferences-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.preference-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.password-change {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 4px;
  margin: 1rem 0;
}

.error-message {
  color: #e74c3c;
  margin: 1rem 0;
  text-align: center;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 2rem;
}

@media (max-width: 768px) {
  .profile-editor {
    padding: 1rem;
  }

  .avatar-section {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
}
</style>
