<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '../stores/project'
import api from '../api'

const router = useRouter()
const store = useProjectStore()

const isDragging = ref(false)
const uploadedFiles = ref([])
const uploadProgress = ref(0)
const isUploading = ref(false)

// 处理拖拽
const handleDragOver = (e) => {
  e.preventDefault()
  isDragging.value = true
}

const handleDragLeave = () => {
  isDragging.value = false
}

const handleDrop = (e) => {
  e.preventDefault()
  isDragging.value = false
  
  const items = e.dataTransfer.items
  const files = []
  
  for (let i = 0; i < items.length; i++) {
    const item = items[i]
    if (item.kind === 'file') {
      const file = item.getAsFile()
      if (file.type.startsWith('image/')) {
        files.push(file)
      }
    }
  }
  
  if (files.length > 0) {
    addFiles(files)
  }
}

// 文件选择
const handleFileSelect = (e) => {
  const files = Array.from(e.target.files).filter(f => f.type.startsWith('image/'))
  addFiles(files)
}

// 添加文件
const addFiles = (files) => {
  const newFiles = files.map(file => ({
    id: Date.now() + Math.random(),
    file,
    name: file.name,
    size: file.size,
    preview: URL.createObjectURL(file)
  }))
  uploadedFiles.value = [...uploadedFiles.value, ...newFiles]
}

// 移除文件
const removeFile = (id) => {
  const file = uploadedFiles.value.find(f => f.id === id)
  if (file) {
    URL.revokeObjectURL(file.preview)
  }
  uploadedFiles.value = uploadedFiles.value.filter(f => f.id !== id)
}

// 清空所有
const clearAll = () => {
  uploadedFiles.value.forEach(f => URL.revokeObjectURL(f.preview))
  uploadedFiles.value = []
}

// 计算属性
const totalSize = computed(() => {
  const bytes = uploadedFiles.value.reduce((sum, f) => sum + f.size, 0)
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
})

const displayImages = computed(() => {
  return uploadedFiles.value.slice(0, 6)
})

const remainingCount = computed(() => {
  return Math.max(0, uploadedFiles.value.length - 6)
})

// 开始分析
const startAnalysis = async () => {
  if (uploadedFiles.value.length === 0) return
  
  isUploading.value = true
  uploadProgress.value = 0
  
  try {
    // 准备FormData
    const formData = new FormData()
    uploadedFiles.value.forEach(f => {
      formData.append('files', f.file)
    })
    
    // 真正上传到服务器
    const response = await api.upload.uploadImages(formData, (progressEvent) => {
      if (progressEvent.total) {
        uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total)
      }
    })
    
    // 服务器返回的数据包含 project_id 和 images (带 preview_url)
    const { project_id, images } = response
    
    // 更新store，使用服务器返回的数据
    store.setProjectId(project_id)
    store.setUploadedImages(images.map(img => ({
      id: img.id,
      name: img.original_name || img.filename,
      filename: img.filename,
      size: img.file_size,
      width: img.width,
      height: img.height,
      preview: img.preview_url,  // 现在是服务器URL，不是blob URL
      preview_url: img.preview_url,
      previewUrl: img.preview_url
    })))
    store.setCurrentStep(2)
    
    // 上传成功后，清理本地blob URLs
    uploadedFiles.value.forEach(f => {
      if (f.preview && f.preview.startsWith('blob:')) {
        URL.revokeObjectURL(f.preview)
      }
    })
    
    isUploading.value = false
    router.push('/analysis')
  } catch (error) {
    console.error('上传失败:', error)
    isUploading.value = false
    alert('上传失败，请重试: ' + (error.message || '未知错误'))
  }
}
</script>

<template>
  <div class="max-w-4xl mx-auto animate-fade-in">
    <!-- 标题 -->
    <div class="text-center mb-8">
      <h1 class="text-2xl font-bold text-text-primary mb-2">上传巡检图像</h1>
      <p class="text-brand-muted text-sm">支持拖拽上传图片或文件夹，支持 JPG、PNG、TIFF 等常见格式</p>
    </div>
    
    <!-- 上传区域 -->
    <div 
      class="glass-card p-8 mb-6 transition-all duration-300"
      :class="{
        'upload-active': isDragging,
        'upload-dashed': uploadedFiles.length === 0
      }"
      @dragover="handleDragOver"
      @dragleave="handleDragLeave"
      @drop="handleDrop"
    >
      <!-- 空状态 -->
      <div v-if="uploadedFiles.length === 0" class="text-center py-12">
        <div class="upload-icon">
          <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        </div>
        <h3 class="text-lg font-semibold text-text-primary mb-2">拖拽图片到这里</h3>
        <p class="text-brand-muted text-sm mb-6">或者点击下方按钮选择文件</p>
        
        <label class="btn-primary cursor-pointer inline-flex items-center">
          <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          选择图片
          <input 
            type="file" 
            class="hidden" 
            multiple 
            accept="image/*"
            @change="handleFileSelect"
          >
        </label>
      </div>
      
      <!-- 已上传的图片 -->
      <div v-else>
        <!-- 图片堆叠预览 -->
        <div class="relative h-48 mb-6 flex items-center justify-center">
          <div class="relative w-64 h-40">
            <div 
              v-for="(img, index) in displayImages" 
              :key="img.id"
              class="img-stack-item"
              :style="{
                width: '160px',
                height: '120px',
                left: `${index * 25}px`,
                top: `${index * 8}px`,
                transform: `rotate(${(index - 2.5) * 3}deg)`,
                zIndex: displayImages.length - index
              }"
            >
              <img :src="img.preview" :alt="img.name" class="w-full h-full object-cover">
            </div>
            
            <!-- 剩余数量提示 -->
            <div 
              v-if="remainingCount > 0"
              class="count-badge"
            >
              +{{ remainingCount }}
            </div>
          </div>
        </div>
        
        <!-- 统计信息 -->
        <div class="flex items-center justify-center gap-8 mb-6">
          <div class="text-center">
            <div class="text-3xl font-bold text-text-primary">{{ uploadedFiles.length }}</div>
            <div class="text-xs text-brand-muted">张图片</div>
          </div>
          <div class="w-px h-10 bg-line-light"></div>
          <div class="text-center">
            <div class="text-3xl font-bold text-text-primary">{{ totalSize }}</div>
            <div class="text-xs text-brand-muted">总大小</div>
          </div>
        </div>
        
        <!-- 操作按钮 -->
        <div class="flex items-center justify-center gap-4">
          <label class="btn-secondary cursor-pointer">
            <svg class="w-4 h-4 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            继续添加
            <input 
              type="file" 
              class="hidden" 
              multiple 
              accept="image/*"
              @change="handleFileSelect"
            >
          </label>
          
          <button @click="clearAll" class="btn-secondary">
            <svg class="w-4 h-4 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            清空全部
          </button>
        </div>
      </div>
    </div>
    
    <!-- 上传进度 -->
    <div v-if="isUploading" class="glass-card p-6 mb-6">
      <div class="flex items-center justify-between mb-2">
        <span class="text-brand-muted text-sm">正在上传...</span>
        <span class="text-brand-primary font-mono font-bold">{{ Math.round(uploadProgress) }}%</span>
      </div>
      <div class="progress-bar">
        <div 
          class="progress-fill"
          :style="{ width: `${uploadProgress}%` }"
        ></div>
      </div>
    </div>
    
    <!-- 下一步按钮 -->
    <div class="flex justify-end">
      <button 
        @click="startAnalysis"
        :disabled="uploadedFiles.length === 0 || isUploading"
        class="btn-primary"
      >
        <span v-if="!isUploading">开始场景分析</span>
        <span v-else>上传中...</span>
        <svg class="w-5 h-5 ml-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
        </svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.upload-active {
  border: 2px solid var(--brand) !important;
  background: rgba(16,35,117,0.05) !important;
}

.upload-dashed {
  border: 1px dashed var(--line) !important;
}

.upload-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 24px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(16,35,117,0.15), rgba(115,162,243,0.1));
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--brand);
}

.img-stack-item {
  position: absolute;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  border: 1px solid rgba(0,0,0,0.1);
  transition: all 0.3s ease;
}

.img-stack-item:hover {
  z-index: 50 !important;
  transform: scale(1.1) rotate(0deg) !important;
}

.count-badge {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: #102375;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-weight: 800;
  font-size: 16px;
  box-shadow: 0 4px 12px rgba(16,35,117,0.3);
  z-index: 100;
}

.progress-bar {
  height: 8px;
  background: rgba(245,245,245,0.8);
  border-radius: 999px;
  overflow: hidden;
  border: 1px solid var(--line-light);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--brand), var(--good));
  border-radius: 999px;
  transition: width 0.3s ease;
}

.bg-line-light {
  background: var(--line-light);
}
</style>

