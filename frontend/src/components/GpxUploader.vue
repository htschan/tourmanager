<template>
  <div class="dropzone-container">
    <div 
      class="dropzone" 
      :class="{ 'active': isDragging, 'error': error }"
      @dragenter="onDragEnter"
      @dragleave="onDragLeave"
      @dragover.prevent
      @drop="onDrop"
      @click="openFileDialog"
    >
      <input 
        type="file" 
        ref="fileInput" 
        class="file-input" 
        @change="onFileSelect"
        :multiple="multiple"
        accept=".gpx"
        hidden
      >
      
      <div v-if="!files.length" class="dropzone-placeholder">
        <div class="icon">
          <i class="fas fa-cloud-upload-alt"></i>
        </div>
        <div class="text">
          <h3>Drop your GPX files here</h3>
          <p>or click to browse your files</p>
        </div>
      </div>
      
      <div v-else class="file-list">
        <div 
          v-for="(file, index) in files" 
          :key="index"
          class="file-item"
        >
          <div class="file-info">
            <span class="file-name">{{ file.name }}</span>
            <span class="file-size">({{ formatFileSize(file.size) }})</span>
          </div>
          <button class="remove-btn" @click.stop="removeFile(index)">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="dropzone-actions" v-if="files.length && !uploading">
          <button class="upload-btn" @click.stop="uploadFiles">
            Upload {{ files.length }} file{{ files.length > 1 ? 's' : '' }}
          </button>
          <button class="clear-btn" @click.stop="clearFiles">
            Clear all
          </button>
        </div>
      </div>
      
      <div v-if="uploading" class="upload-progress">
        <div class="progress-bar">
          <div class="progress" :style="{ width: `${uploadProgress}%` }"></div>
        </div>
        <span class="progress-text">{{ uploadProgress }}% Complete</span>
      </div>
      
      <div v-if="error" class="error-message">
        {{ error }}
      </div>
    </div>
    
    <div v-if="uploadResults.length" class="upload-results">
      <h3>Upload Results</h3>
      <ul class="results-list">
        <li 
          v-for="(result, index) in uploadResults" 
          :key="index"
          :class="result.status"
        >
          <span class="result-filename">{{ result.filename }}</span>
          <span class="result-message">{{ result.message }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import axios from 'axios';
import { api } from '../services/api';
import { useAuthStore } from '../stores/auth';

const props = defineProps({
  multiple: {
    type: Boolean,
    default: true
  },
  maxFileSize: {
    type: Number,
    default: 10 * 1024 * 1024 // 10MB
  }
});

const emit = defineEmits(['upload-success', 'upload-error']);

const fileInput = ref(null);
const isDragging = ref(false);
const files = reactive([]);
const error = ref('');
const uploading = ref(false);
const uploadProgress = ref(0);
const uploadResults = ref([]);
const authStore = useAuthStore();

const onDragEnter = () => {
  isDragging.value = true;
  error.value = '';
};

const onDragLeave = () => {
  isDragging.value = false;
};

const onDrop = (e) => {
  e.preventDefault();
  isDragging.value = false;
  error.value = '';
  
  const droppedFiles = Array.from(e.dataTransfer.files);
  
  // Filter for only GPX files
  const validFiles = droppedFiles.filter(file => {
    const isGpx = file.name.toLowerCase().endsWith('.gpx');
    if (!isGpx) {
      error.value = 'Only GPX files are accepted';
    }
    return isGpx;
  });
  
  // Check file size
  validFiles.forEach(file => {
    if (file.size > props.maxFileSize) {
      error.value = `File ${file.name} exceeds maximum size of ${formatFileSize(props.maxFileSize)}`;
      return;
    }
    
    // Add file if not already added
    const exists = files.some(f => f.name === file.name && f.size === file.size);
    if (!exists) {
      files.push(file);
    }
  });
};

const onFileSelect = (e) => {
  error.value = '';
  const selectedFiles = Array.from(e.target.files);
  
  // Filter for only GPX files
  const validFiles = selectedFiles.filter(file => {
    const isGpx = file.name.toLowerCase().endsWith('.gpx');
    if (!isGpx) {
      error.value = 'Only GPX files are accepted';
    }
    return isGpx;
  });
  
  // Check file size
  validFiles.forEach(file => {
    if (file.size > props.maxFileSize) {
      error.value = `File ${file.name} exceeds maximum size of ${formatFileSize(props.maxFileSize)}`;
      return;
    }
    
    // Add file if not already added
    const exists = files.some(f => f.name === file.name && f.size === file.size);
    if (!exists) {
      files.push(file);
    }
  });
  
  // Reset the input so the same file can be selected again if needed
  fileInput.value.value = null;
};

const openFileDialog = () => {
  fileInput.value.click();
};

const removeFile = (index) => {
  files.splice(index, 1);
};

const clearFiles = () => {
  files.splice(0, files.length);
  error.value = '';
};

const uploadFiles = async () => {
  if (!files.length) {
    error.value = 'No files to upload';
    return;
  }
  
  uploading.value = true;
  uploadProgress.value = 0;
  uploadResults.value = [];
  error.value = '';
  
  try {
    const formData = new FormData();
    
    if (props.multiple) {
      // For batch upload
      files.forEach(file => {
        formData.append('files', file);
      });
      
      const config = {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': authStore.token ? `Bearer ${authStore.token}` : ''
        },
        onUploadProgress: (progressEvent) => {
          uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        }
      };
      
      const response = await api.post('/api/tours/upload/batch', formData, config);
      uploadResults.value = response.data.results || [];
      emit('upload-success', response.data);
    } else {
      // For single file upload
      formData.append('file', files[0]);
      
      const config = {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': authStore.token ? `Bearer ${authStore.token}` : ''
        },
        onUploadProgress: (progressEvent) => {
          uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        }
      };
      
      const response = await api.post('/api/tours/upload', formData, config);
      uploadResults.value = [{
        filename: files[0].name,
        status: response.data.status,
        message: response.data.message
      }];
      emit('upload-success', response.data);
    }
    
    // Clear files after successful upload
    files.splice(0, files.length);
    
  } catch (err) {
    console.error('Upload error:', err);
    error.value = `Upload failed: ${err.response?.data?.detail || err.message || 'Unknown error'}`;
    emit('upload-error', err);
  } finally {
    uploading.value = false;
  }
};

const formatFileSize = (size) => {
  if (size < 1024) {
    return `${size} B`;
  } else if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(2)} KB`;
  } else {
    return `${(size / (1024 * 1024)).toFixed(2)} MB`;
  }
};
</script>

<style scoped>
.dropzone-container {
  margin: 20px 0;
  width: 100%;
}

.dropzone {
  border: 2px dashed #ccc;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  background: #f9f9f9;
  cursor: pointer;
  transition: all 0.3s ease;
}

.dropzone:hover {
  border-color: #2196f3;
  background: #f0f8ff;
}

.dropzone.active {
  border-color: #2196f3;
  background: #e3f2fd;
}

.dropzone.error {
  border-color: #ff5252;
  background: #ffebee;
}

.dropzone-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.icon {
  font-size: 48px;
  color: #2196f3;
  margin-bottom: 16px;
}

.text h3 {
  margin: 0 0 8px;
  font-weight: 500;
  color: #333;
}

.text p {
  margin: 0;
  color: #777;
}

.file-list {
  max-height: 300px;
  overflow-y: auto;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #fff;
  border-radius: 4px;
  margin-bottom: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.file-info {
  display: flex;
  align-items: center;
}

.file-name {
  font-weight: 500;
  margin-right: 8px;
}

.file-size {
  color: #777;
  font-size: 0.9em;
}

.remove-btn {
  background: none;
  border: none;
  color: #f44336;
  cursor: pointer;
  font-size: 16px;
}

.dropzone-actions {
  margin-top: 16px;
  display: flex;
  justify-content: center;
  gap: 12px;
}

.upload-btn, .clear-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.upload-btn {
  background-color: #2196f3;
  color: white;
}

.upload-btn:hover {
  background-color: #1976d2;
}

.clear-btn {
  background-color: #e0e0e0;
  color: #333;
}

.clear-btn:hover {
  background-color: #d5d5d5;
}

.upload-progress {
  margin-top: 20px;
}

.progress-bar {
  height: 8px;
  background-color: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress {
  height: 100%;
  background-color: #4caf50;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 0.9em;
  color: #777;
}

.error-message {
  margin-top: 16px;
  color: #f44336;
  font-weight: 500;
}

.upload-results {
  margin-top: 24px;
  border-top: 1px solid #e0e0e0;
  padding-top: 16px;
}

.results-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.results-list li {
  padding: 8px 12px;
  border-radius: 4px;
  margin-bottom: 8px;
  display: flex;
  justify-content: space-between;
}

.results-list li.success {
  background-color: #e8f5e9;
  color: #2e7d32;
}

.results-list li.warning {
  background-color: #fff3e0;
  color: #ef6c00;
}

.results-list li.error {
  background-color: #ffebee;
  color: #c62828;
}

.result-filename {
  font-weight: 500;
}
</style>
