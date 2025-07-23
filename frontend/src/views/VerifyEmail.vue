<template>
  <div class="verify-email-container">
    <div class="card">
      <div v-if="loading" class="status-indicator loading">
        <div class="spinner"></div>
        <h2>Verifying your email...</h2>
        <p>Please wait while we verify your email address.</p>
      </div>
      
      <div v-else-if="verified" class="status-indicator success">
        <div class="icon-circle success">✓</div>
        <h2>Email Verified Successfully!</h2>
        <p>Your email has been verified. Your account is now awaiting admin approval.</p>
        <p>You will receive a notification email once your account is approved.</p>
        <router-link to="/login" class="btn btn-primary">Go to Login</router-link>
      </div>
      
      <div v-else class="status-indicator error">
        <div class="icon-circle error">✗</div>
        <h2>Verification Failed</h2>
        <p>{{ errorMessage || 'There was a problem verifying your email address.' }}</p>
        <p>Please try again or contact support if the problem persists.</p>
        <router-link to="/login" class="btn btn-secondary">Go to Login</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import { useUserStore } from '../stores/users';

const route = useRoute();
const userStore = useUserStore();

const loading = ref(true);
const verified = ref(false);
const errorMessage = ref('');

onMounted(async () => {
  // Get the token from the URL query parameter
  const token = route.query.token;
  
  console.log('VerifyEmail component mounted');
  console.log('Route query:', route.query);
  console.log('Token extracted:', token);
  
  if (!token) {
    console.error('No token found in URL');
    loading.value = false;
    errorMessage.value = 'Missing verification token.';
    return;
  }
  
  try {
    console.log('Calling userStore.verifyEmail with token:', token);
    // Call the API to verify the email
    const result = await userStore.verifyEmail(token);
    console.log('Verification successful:', result);
    verified.value = true;
  } catch (error) {
    console.error('Verification failed:', error);
    console.error('Error response:', error.response);
    errorMessage.value = error.response?.data?.detail || 'Invalid or expired verification token';
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.verify-email-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
  padding: 2rem;
}

.card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  padding: 2rem;
  max-width: 500px;
  width: 100%;
  text-align: center;
}

.status-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 5px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top-color: #3498db;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.icon-circle {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  margin-bottom: 1rem;
}

.icon-circle.success {
  background-color: #d4edda;
  color: #155724;
}

.icon-circle.error {
  background-color: #f8d7da;
  color: #721c24;
}

h2 {
  margin-bottom: 1rem;
  font-weight: 600;
}

p {
  margin-bottom: 1rem;
  color: #6c757d;
}

.btn {
  display: inline-block;
  padding: 0.5rem 1.5rem;
  border: none;
  border-radius: 4px;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  margin-top: 1rem;
}

.btn-primary {
  background-color: #3498db;
  color: white;
}

.btn-secondary {
  background-color: #e9ecef;
  color: #495057;
}
</style>
