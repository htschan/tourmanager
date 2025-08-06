<template>
  <div class="dropzone-container">
    <!-- Upload instructions -->
    <div class="upload-instructions">
      <p>Drop your GPX, KML or KMZ files here.</p>
    </div>
    
    <!-- File input completely separate from the dropzone -->
    <input 
      type="file" 
      ref="fileInput" 
      class="file-input" 
      @change="onFileSelect"
      :multiple="multiple"
      accept=".gpx,.kml,.kmz"
      style="display: none;"
    >
      
    <div 
      class="dropzone" 
      :class="{ 'active': isDragging, 'error': error }"
      @dragenter="onDragEnter"
      @dragleave="onDragLeave"
      @dragover.prevent
      @drop="onDrop"
      @click="openFileDialog"
    >
      <div v-if="!files.length" class="dropzone-placeholder">
        <div class="icon">
          <i class="fas fa-cloud-upload-alt"></i>
        </div>
        <div class="text">
          <h3>Drop your GPX, KML or KMZ files here</h3>
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
import { ref, reactive, computed } from 'vue';
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

// No longer need to check for admin role, any authenticated user can upload

const fileInput = ref(null);
const isDragging = ref(false);
const files = reactive([]);
const error = ref('');
const uploading = ref(false);
const uploadProgress = ref(0);
const uploadResults = ref([]);
const authStore = useAuthStore();

const onDragEnter = () => {
  console.log('onDragEnter event triggered');
  isDragging.value = true;
  error.value = '';
};

const onDragLeave = () => {
  console.log('onDragLeave event triggered');
  isDragging.value = false;
};

const onDrop = (e) => {
  console.log('onDrop event triggered');
  e.preventDefault();
  isDragging.value = false;
  error.value = '';
  
  const droppedFiles = Array.from(e.dataTransfer.files);
  console.log(`Dropped ${droppedFiles.length} files:`, droppedFiles);
  
  // Filter for GPX and KML files
  const validFiles = droppedFiles.filter(file => {
    const fileName = file.name.toLowerCase();
    console.log(`Checking file: ${fileName}, type: ${file.type}`);
    
    // Accept by extension and optionally by MIME type
    const validExtension = fileName.endsWith('.gpx') || fileName.endsWith('.kml') || fileName.endsWith('.kmz');
    const validMimeType = file.type === 'application/gpx+xml' || 
                         file.type === 'application/vnd.google-earth.kml+xml' ||
                         file.type === 'application/vnd.google-earth.kmz' ||
                         file.type === 'application/zip' ||
                         file.type === 'application/xml' ||
                         file.type === 'application/octet-stream' ||
                         file.type === 'text/xml';
    
    const isValid = validExtension || validMimeType;
    
    if (!isValid) {
      console.warn(`Rejected file: ${fileName}, type: ${file.type}`);
      error.value = 'Only GPX, KML and KMZ files are accepted';
    }
    return isValid;
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
  
  // Filter for GPX and KML files
  const validFiles = selectedFiles.filter(file => {
    const fileName = file.name.toLowerCase();
    console.log(`Checking selected file: ${fileName}, type: ${file.type}`);
    
    // Accept by extension and optionally by MIME type
    const validExtension = fileName.endsWith('.gpx') || fileName.endsWith('.kml') || fileName.endsWith('.kmz');
    const validMimeType = file.type === 'application/gpx+xml' || 
                         file.type === 'application/vnd.google-earth.kml+xml' ||
                         file.type === 'application/vnd.google-earth.kmz' ||
                         file.type === 'application/zip' ||
                         file.type === 'application/xml' ||
                         file.type === 'application/octet-stream' ||
                         file.type === 'text/xml';
    
    const isValid = validExtension || validMimeType;
    
    if (!isValid) {
      console.warn(`Rejected selected file: ${fileName}, type: ${file.type}`);
      error.value = 'Only GPX, KML and KMZ files are accepted';
    }
    return isValid;
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
  console.log('openFileDialog called', fileInput.value);
  if (fileInput.value) {
    console.log('Clicking file input element');
    fileInput.value.click();
  } else {
    console.error('File input reference is null');
  }
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
    console.log('Starting file upload process');
    const formData = new FormData();
    
    if (props.multiple) {
      // For batch upload
      console.log(`Preparing to upload ${files.length} files in batch mode`);
      files.forEach((file, index) => {
        console.log(`Adding file ${index + 1}/${files.length} to form data: ${file.name} (${file.type}, ${file.size} bytes)`);
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
    
    // Enhanced error logging
    if (err.response) {
      // The request was made and the server responded with a status code outside of 2xx
      console.error('Error response from server:', {
        status: err.response.status,
        statusText: err.response.statusText,
        data: err.response.data,
        headers: err.response.headers
      });
    } else if (err.request) {
      // The request was made but no response was received
      console.error('No response received:', err.request);
    } else {
      // Something happened in setting up the request
      console.error('Error setting up request:', err.message);
    }
    
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

.standard-file-input-container {
  margin: 0 auto 20px;
  width: 100%;
  max-width: 300px;
  text-align: center;
}

.standard-file-input {
  width: 100%;
  padding: 10px;
  border: 2px solid #4caf50;
  border-radius: 4px;
  background-color: white;
  color: #333;
  font-size: 14px;
  cursor: pointer;
}

.upload-instructions {
  background-color: #e3f2fd;
  padding: 16px;
  margin-bottom: 20px;
  border-radius: 4px;
  text-align: center;
  border-left: 4px solid #2196f3;
}

.upload-instructions p {
  margin: 0;
  color: #333;
  font-weight: 500;
}
</style>
