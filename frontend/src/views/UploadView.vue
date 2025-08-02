<template>
  <div class="upload-page">
    <h1>Tour Upload (GPX/KML)</h1>
    
    <div class="intro-section">
      <div class="upload-notice">
        <p>
          Upload your GPX tour files to add them to the database. You can drag and drop multiple files at once.
        </p>
      </div>
      
      <div class="tips">
        <h3>Tips</h3>
        <ul>
          <li>GPX and KML files are accepted</li>
          <li>Maximum file size: 10MB per file</li>
          <li>Duplicate tours (same Komoot ID) will be detected automatically</li>
        </ul>
      </div>
    </div>
    
    <GpxUploader 
      @upload-success="handleUploadSuccess"
      @upload-error="handleUploadError"
    />
    
    <div v-if="showUploadStats" class="upload-stats">
      <h2>Upload Statistics</h2>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-value">{{ uploadStats.totalFiles }}</div>
          <div class="stat-label">Total Files</div>
        </div>
        <div class="stat-card success">
          <div class="stat-value">{{ uploadStats.success }}</div>
          <div class="stat-label">Successful</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-value">{{ uploadStats.warning }}</div>
          <div class="stat-label">Warnings</div>
        </div>
        <div class="stat-card error">
          <div class="stat-value">{{ uploadStats.error }}</div>
          <div class="stat-label">Errors</div>
        </div>
      </div>
    </div>
    
    <div class="actions">
      <router-link to="/" class="home-link">
        <button class="btn-secondary">
          Back to Home
        </button>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import GpxUploader from '../components/GpxUploader.vue';
import { useAuthStore } from '../stores/auth';

const showUploadStats = ref(false);
const uploadStats = reactive({
  totalFiles: 0,
  success: 0,
  warning: 0,
  error: 0
});

const authStore = useAuthStore();

const handleUploadSuccess = (data) => {
  if (data.results) {
    // Calculate statistics
    showUploadStats.value = true;
    uploadStats.totalFiles = data.results.length;
    uploadStats.success = data.results.filter(r => r.status === 'success').length;
    uploadStats.warning = data.results.filter(r => r.status === 'warning').length;
    uploadStats.error = data.results.filter(r => r.status === 'error').length;
  } else {
    // Single file upload
    showUploadStats.value = true;
    uploadStats.totalFiles = 1;
    uploadStats.success = data.status === 'success' ? 1 : 0;
    uploadStats.warning = data.status === 'warning' ? 1 : 0;
    uploadStats.error = data.status === 'error' ? 1 : 0;
  }
};

const handleUploadError = (error) => {
  console.error('Upload failed:', error);
};
</script>

<style scoped>
.upload-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}

h1 {
  margin-bottom: 24px;
  color: #2c3e50;
}

.upload-notice {
  background-color: #e8f5e9;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
  border-left: 4px solid #4caf50;
}

h1 {
  border-bottom: 2px solid #e0e0e0;
  padding-bottom: 12px;
}

.intro-section {
  margin-bottom: 32px;
  background-color: #f5f5f5;
  padding: 20px;
  border-radius: 8px;
}

.intro-section p {
  margin-top: 0;
}

.tips {
  background-color: #e3f2fd;
  padding: 16px;
  border-radius: 4px;
  margin-top: 16px;
}

.tips h3 {
  margin-top: 0;
  margin-bottom: 8px;
  color: #1976d2;
}

.tips ul {
  margin: 0;
  padding-left: 20px;
}

.tips li {
  margin-bottom: 4px;
}

.upload-stats {
  margin-top: 40px;
  background-color: #f5f5f5;
  padding: 20px;
  border-radius: 8px;
}

.upload-stats h2 {
  margin-top: 0;
  color: #2c3e50;
  margin-bottom: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 16px;
}

.stat-card {
  background-color: #fff;
  padding: 16px;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.stat-card.success {
  background-color: #e8f5e9;
}

.stat-card.warning {
  background-color: #fff3e0;
}

.stat-card.error {
  background-color: #ffebee;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 4px;
}



.stat-label {
  color: #777;
  font-size: 14px;
}

.actions {
  margin-top: 32px;
  display: flex;
  justify-content: flex-end;
}

.btn-secondary {
  padding: 8px 16px;
  background-color: #e0e0e0;
  color: #333;
  border: none;
  border-radius: 4px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  background-color: #d5d5d5;
}
</style>
