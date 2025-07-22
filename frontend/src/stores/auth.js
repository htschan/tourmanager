import { defineStore } from 'pinia';
import { api } from '../services/api';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('token') || null,
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.token,
    getUser: (state) => state.user,
    isAdmin: (state) => state.user?.role === 'admin',
  },
  
  actions: {
    async login(username, password) {
      try {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);
        
        const response = await api.post('/token', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        
        this.token = response.data.access_token;
        localStorage.setItem('token', response.data.access_token);
        
        // Fetch user data
        await this.fetchUser();
        
        return { success: true };
      } catch (error) {
        console.error('Login error:', error);
        // Check if this is a pending approval error
        if (error.response?.status === 403 && error.response?.data?.detail?.includes('pending approval')) {
          return { 
            success: false, 
            message: 'Your account is pending approval by an administrator. Please check back later.'
          };
        }
        return { 
          success: false, 
          message: 'Invalid username or password'
        };
      }
    },
    
    async fetchUser() {
      try {
        const response = await api.get('/users/me');
        this.user = response.data;
      } catch (error) {
        console.error('Fetch user error:', error);
        this.logout();
        throw error;
      }
    },
    
    logout(expiredSession = false) {
      this.token = null;
      this.user = null;
      localStorage.removeItem('token');
      
      // If session expired, we'll add the notification message when redirecting
      if (expiredSession) {
        // This could be enhanced to use a toast notification system
        console.warn('Session expired. Please login again.');
      }
    },
    
    async register(userData) {
      try {
        const response = await api.post('/api/auth/register', userData);
        return { success: true, message: 'Registration successful! Please wait for admin approval.' };
      } catch (error) {
        console.error('Registration error:', error);
        throw new Error(error.response?.data?.detail || 'Registration failed');
      }
    },
    
    async changePassword(currentPassword, newPassword) {
      try {
        const response = await api.post('/api/auth/change-password', {
          current_password: currentPassword,
          new_password: newPassword
        });
        return { success: true, message: response.data.message };
      } catch (error) {
        console.error('Password change error:', error);
        const message = error.response?.data?.detail || 'Failed to change password';
        return { success: false, message };
      }
    },
  }
});
