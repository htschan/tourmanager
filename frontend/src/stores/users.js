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
        const response = await api.get('/api/users')
        this.users = response.data
      } catch (error) {
        this.error = error.message
        useToastStore().showError('Failed to load users')
      } finally {
        this.loading = false
      }
    },

    async registerUser(userData) {
      this.loading = true
      try {
        const response = await api.post('/api/auth/register', userData)
        useToastStore().showSuccess('Registration successful! Waiting for admin approval.')
        return response.data
      } catch (error) {
        this.error = error.message
        useToastStore().showError('Registration failed: ' + error.message)
        throw error
      } finally {
        this.loading = false
      }
    },

    async updateUserStatus(username, status) {
      this.loading = true
      try {
        const response = await api.patch(`/api/users/${username}/status`, JSON.stringify(status))
        const updatedUser = response.data
        const index = this.users.findIndex(u => u.username === username)
        if (index !== -1) {
          this.users[index] = updatedUser
        }
        useToastStore().showSuccess(`User ${username} status updated to ${status}`)
        return updatedUser
      } catch (error) {
        this.error = error.message
        useToastStore().showError('Failed to update user status')
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
        useToastStore().showError('Failed to load profile')
        throw error
      }
    },

    async updateProfile(profileData) {
      this.loading = true
      try {
        const response = await api.patch('/users/me', profileData)
        useToastStore().showSuccess('Profile updated successfully')
        return response.data
      } catch (error) {
        useToastStore().showError('Failed to update profile')
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
        useToastStore().showSuccess('Avatar uploaded successfully')
        return response.data
      } catch (error) {
        useToastStore().showError('Failed to upload avatar')
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
    }
  }
})
