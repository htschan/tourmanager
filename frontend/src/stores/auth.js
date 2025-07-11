import { defineStore } from 'pinia';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('token') || null,
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.token,
    getUser: (state) => state.user,
  },
  
  actions: {
    async login(username, password) {
      try {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);
        
        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/token`, {
          method: 'POST',
          body: formData,
        });
        
        if (!response.ok) {
          throw new Error('Login failed');
        }
        
        const data = await response.json();
        this.token = data.access_token;
        localStorage.setItem('token', data.access_token);
        
        // Fetch user data
        await this.fetchUser();
        
        return true;
      } catch (error) {
        console.error('Login error:', error);
        return false;
      }
    },
    
    async fetchUser() {
      try {
        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/users/me`, {
          headers: {
            'Authorization': `Bearer ${this.token}`
          }
        });
        
        if (!response.ok) {
          throw new Error('Failed to fetch user data');
        }
        
        this.user = await response.json();
      } catch (error) {
        console.error('Fetch user error:', error);
        this.logout();
      }
    },
    
    logout() {
      this.token = null;
      this.user = null;
      localStorage.removeItem('token');
    }
  }
});
