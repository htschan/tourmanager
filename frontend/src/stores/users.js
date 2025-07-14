import { defineStore } from 'pinia'
import { api } from '../services/api'
import { useToastStore } from './toast'

export const useUserStore = defineStore('users', {
  state: () => ({
    users: [],
    loading: false,
    error: null
  }),

  actions: {
    async fetchUsers() {
      this.loading = true
      try {
        console.log('🔍 Fetching users from API...')
        const response = await api.get('/api/users')
        console.log('🔍 API Response:', response)
        this.users = response.data
        return this.users
      } catch (error) {
        console.error('❌ API Error:', error)
        this.error = error.message
        useToastStore().error('Failed to load users')
        return []
      } finally {
        this.loading = false
      }
    },

    async registerUser(userData) {
      this.loading = true
      try {
        const response = await api.post('/api/auth/register', userData)
        useToastStore().success('Registration successful! Waiting for admin approval.')
        return response.data
      } catch (error) {
        this.error = error.message
        useToastStore().error('Registration failed: ' + error.message)
        throw error
      } finally {
        this.loading = false
      }
    },

    async updateUserStatus(username, status) {
      this.loading = true
      try {
        console.log('🔍 Sending status update:', { status })
        const response = await api.patch(`/api/users/${username}/status`, { status: status })
        const updatedUser = response.data
        const index = this.users.findIndex(u => u.username === username)
        if (index !== -1) {
          this.users[index] = updatedUser
        }
        useToastStore().success(`User ${username} status updated to ${status}`)
        return updatedUser
      } catch (error) {
        this.error = error.message
        useToastStore().error('Failed to update user status')
        throw error
      } finally {
        this.loading = false
      }
    },

    async fetchProfile() {
      try {
        const response = await api.get('/users/me')
        return response.data
      } catch (error) {
        useToastStore().error('Failed to load profile')
        throw error
      }
    },

    async updateProfile(profileData) {
      this.loading = true
      try {
        const response = await api.patch('/users/me', profileData)
        useToastStore().success('Profile updated successfully')
        return response.data
      } catch (error) {
        useToastStore().error('Failed to update profile')
        throw error
      } finally {
        this.loading = false
      }
    },

    async uploadAvatar(formData) {
      this.loading = true
      try {
        const response = await api.post('/users/me/avatar', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        useToastStore().success('Avatar uploaded successfully')
        return response.data
      } catch (error) {
        useToastStore().error('Failed to upload avatar')
        throw error
      } finally {
        this.loading = false
      }
    },

    async requestEmailVerification(email) {
      this.loading = true
      try {
        await api.post('/request-verification', { email })
        useToastStore().showSuccess('Verification email sent')
      } catch (error) {
        useToastStore().showError('Failed to send verification email')
        throw error
      } finally {
        this.loading = false
      }
    },

    async requestPasswordReset(email) {
      try {
        await api.post('/request-password-reset', { email })
        useToastStore().showSuccess('Password reset email sent')
      } catch (error) {
        useToastStore().showError('Failed to send password reset email')
        throw error
      }
    },

    async resetPassword(token, newPassword) {
      try {
        await api.post('/reset-password', { token, new_password: newPassword })
        useToastStore().showSuccess('Password reset successfully')
      } catch (error) {
        useToastStore().showError('Failed to reset password')
        throw error
      }
    },

    async verifyEmail(token) {
      try {
        await api.post('/verify-email', { token })
        useToastStore().showSuccess('Email verified successfully')
      } catch (error) {
        useToastStore().showError('Failed to verify email')
        throw error
      }
    },

    async deleteUser(username) {
      this.loading = true
      try {
        await api.delete(`/api/users/${username}`)
        // Remove user from local state
        this.users = this.users.filter(u => u.username !== username)
        useToastStore().success(`User ${username} has been deleted`)
      } catch (error) {
        this.error = error.message
        useToastStore().error('Failed to delete user')
        throw error
      } finally {
        this.loading = false
      }
    }
  }
})
