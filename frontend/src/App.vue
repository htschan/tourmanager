<template>
  <div id="app">
    <!-- Navigation -->
    <nav class="navbar">
      <div class="nav-container">
        <router-link to="/" class="nav-logo">
          🚴 Tour Manager
        </router-link>
        
        <div class="nav-menu" :class="{ active: isMenuOpen }">
          <router-link to="/" class="nav-link" @click="closeMenu">
            🏠 Home
          </router-link>
          <router-link to="/map" class="nav-link" @click="closeMenu">
            🗺️ Karte
          </router-link>
          <router-link to="/statistics" class="nav-link" @click="closeMenu">
            📊 Statistiken
          </router-link>
          <button class="theme-toggle nav-link" @click="themeStore.toggleTheme">
            {{ themeStore.theme === 'dark' ? '☀️' : '🌙' }}
          </button>
        </div>
        
        <div class="nav-toggle" @click="toggleMenu">
          <span class="bar"></span>
          <span class="bar"></span>
          <span class="bar"></span>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="main-content">
      <router-view />
    </main>

    <!-- Toast Notifications -->
    <div v-if="toastStore.toasts.length" class="toast-container">
      <div
        v-for="toast in toastStore.toasts"
        :key="toast.id"
        :class="['toast', `toast-${toast.type}`]"
      >
        {{ toast.message }}
        <button @click="toastStore.removeToast(toast.id)" class="toast-close">
          ×
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useToastStore } from './stores/toast'
import { useThemeStore } from './stores/theme'

const toastStore = useToastStore()
const themeStore = useThemeStore()
const isMenuOpen = ref(false)

const toggleMenu = () => {
  isMenuOpen.value = !isMenuOpen.value
}

const closeMenu = () => {
  isMenuOpen.value = false
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  /* Light theme */
  --bg-color: #f8f9fa;
  --text-color: #333;
  --nav-bg: #3498db;
  --nav-text: white;
  --card-bg: white;
  --border-color: #dee2e6;
  --hover-bg: #e9ecef;
}

:root[data-theme="dark"] {
  /* Dark theme */
  --bg-color: #1a1a1a;
  --text-color: #e0e0e0;
  --nav-bg: #2c3e50;
  --nav-text: #e0e0e0;
  --card-bg: #2d2d2d;
  --border-color: #404040;
  --hover-bg: #363636;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  line-height: 1.6;
  color: var(--text-color);
  background-color: var(--bg-color);
  transition: background-color 0.3s ease, color 0.3s ease;
}

/* Navigation */
.navbar {
  background: var(--nav-bg);
  color: var(--nav-text);
  padding: 0;
  position: sticky;
  top: 0;
  z-index: 1000;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: background-color 0.3s ease;
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-logo {
  font-size: 1.5rem;
  font-weight: bold;
  color: white;
  text-decoration: none;
}

.nav-menu {
  display: flex;
  gap: 2rem;
  list-style: none;
}

.nav-link {
  color: white;
  text-decoration: none;
  transition: opacity 0.3s;
}

.nav-link:hover,
.nav-link.router-link-active {
  opacity: 0.8;
  text-decoration: underline;
}

.nav-toggle {
  display: none;
  flex-direction: column;
  cursor: pointer;
}

.bar {
  width: 25px;
  height: 3px;
  background-color: white;
  margin: 3px 0;
  transition: 0.3s;
}

/* Main Content */
.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1rem;
  min-height: calc(100vh - 80px);
}

/* Toast Notifications */
.toast-container {
  position: fixed;
  top: 90px;
  right: 20px;
  z-index: 2000;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.toast {
  background: white;
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-width: 300px;
  animation: slideIn 0.3s ease-out;
}

.toast-success {
  border-left: 4px solid #27ae60;
}

.toast-error {
  border-left: 4px solid #e74c3c;
}

.toast-info {
  border-left: 4px solid #3498db;
}

.toast-close {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  margin-left: 1rem;
  opacity: 0.7;
}

.toast-close:hover {
  opacity: 1;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* Cards */
.card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin-bottom: 1rem;
}

.card-header {
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #2c3e50;
}

/* Buttons */
.btn {
  display: inline-block;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.3s;
  font-weight: 500;
}

.btn-primary {
  background: #3498db;
  color: white;
}

.btn-primary:hover {
  background: #2980b9;
  transform: translateY(-2px);
}

.btn-secondary {
  background: #95a5a6;
  color: white;
}

.btn-secondary:hover {
  background: #7f8c8d;
}

.btn-success {
  background: #27ae60;
  color: white;
}

.btn-success:hover {
  background: #229954;
}

/* Form Elements */
.form-group {
  margin-bottom: 1rem;
}

.form-label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #2c3e50;
}

.form-input,
.form-select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.3s;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
}

/* Grid */
.grid {
  display: grid;
  gap: 1rem;
}

.grid-2 {
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
}

.grid-3 {
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
}

/* Responsive Design */
@media (max-width: 768px) {
  .nav-menu {
    position: fixed;
    left: -100%;
    top: 70px;
    flex-direction: column;
    background-color: #3498db;
    width: 100%;
    text-align: center;
    transition: 0.3s;
    box-shadow: 0 10px 27px rgba(0,0,0,0.05);
    padding: 2rem 0;
  }

  .nav-menu.active {
    left: 0;
  }

  .nav-toggle {
    display: flex;
  }

  .main-content {
    padding: 1rem;
  }

  .toast-container {
    right: 10px;
    left: 10px;
  }

  .toast {
    min-width: auto;
  }
}
</style>
