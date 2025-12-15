<script setup>
import { ref, computed, watch } from 'vue'
import { useProjectStore } from '../stores/project'

const store = useProjectStore()

// 浮窗展开/收起状态
const isExpanded = ref(true)

// 是否显示浮窗
const isVisible = computed(() => {
  return store.supplementaryFiles.length > 0 || store.isUploadingSupplementary
})

// 总进度
const totalProgress = computed(() => {
  const files = store.supplementaryFiles
  if (files.length === 0) return 0
  
  const total = files.reduce((sum, file) => sum + (file.progress || 0), 0)
  return Math.round(total / files.length)
})

// 上传状态文本
const statusText = computed(() => {
  if (store.isUploadingSupplementary) {
    const uploading = store.supplementaryFiles.filter(f => f.status === 'uploading').length
    return `正在上传 ${uploading} 个文件...`
  }
  
  const completed = store.supplementaryFiles.filter(f => f.status === 'completed').length
  const total = store.supplementaryFiles.length
  
  if (completed === total) {
    return '所有文件上传完成'
  }
  
  return `${completed}/${total} 个文件已完成`
})

// 获取文件类型图标
const getFileIcon = (type) => {
  const icons = {
    pos: '📍',
    sfm: '📊',
    ortho: '🗺️',
    model3d: '🏛️'
  }
  return icons[type] || '📁'
}

// 获取文件类型名称
const getTypeName = (type) => {
  const names = {
    pos: 'PoS信息',
    sfm: 'SfM结果',
    ortho: '正射影像',
    model3d: '三维模型'
  }
  return names[type] || '未知类型'
}

// 获取状态颜色
const getStatusClass = (status) => {
  switch (status) {
    case 'completed':
      return 'text-accent-success'
    case 'uploading':
      return 'text-brand-sky'
    case 'error':
      return 'text-accent-danger'
    default:
      return 'text-text-primary/50'
  }
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`
}

// 关闭浮窗（清除已完成的上传记录）
const handleClose = () => {
  store.clearCompletedSupplementaryFiles()
}

// 重试失败的上传
const retryUpload = (fileId) => {
  store.retrySupplementaryUpload(fileId)
}

// 取消上传
const cancelUpload = (fileId) => {
  store.cancelSupplementaryUpload(fileId)
}

// 自动收起完成的上传
watch(() => store.isUploadingSupplementary, (isUploading) => {
  if (!isUploading && totalProgress.value === 100) {
    // 上传完成3秒后自动收起
    setTimeout(() => {
      isExpanded.value = false
    }, 3000)
  }
})
</script>

<template>
  <Teleport to="body">
    <transition name="slide-up">
      <div 
        v-if="isVisible"
        class="fixed bottom-4 right-4 z-40"
      >
        <!-- 收起状态 -->
        <div 
          v-if="!isExpanded"
          @click="isExpanded = true"
          class="glass-card p-3 cursor-pointer hover:bg-base-elevated transition-all flex items-center gap-3 min-w-[200px]"
        >
          <div class="relative">
            <svg class="w-6 h-6 text-brand-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <div 
              v-if="store.isUploadingSupplementary"
              class="absolute -top-1 -right-1 w-3 h-3 bg-brand-primary rounded-full animate-pulse"
            ></div>
          </div>
          <div class="flex-1">
            <div class="text-text-primary text-sm font-medium">额外资料上传</div>
            <div class="text-text-secondary  text-xs">{{ statusText }}</div>
          </div>
          <div class="text-brand-sky font-mono font-bold">{{ totalProgress }}%</div>
        </div>
        
        <!-- 展开状态 -->
        <div 
          v-else
          class="glass-card w-80 overflow-hidden"
        >
          <!-- 头部 -->
          <div class="flex items-center justify-between p-4 border-b border-line-light">
            <div class="flex items-center gap-2">
              <svg class="w-5 h-5 text-brand-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <span class="text-text-primary font-medium">额外资料上传</span>
            </div>
            <div class="flex items-center gap-2">
              <button 
                @click="isExpanded = false"
                class="p-1 hover:bg-base-elevated rounded transition-colors"
                title="收起"
              >
                <svg class="w-4 h-4 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              <button
                v-if="!store.isUploadingSupplementary"
                @click="handleClose"
                class="p-1 hover:bg-base-elevated rounded transition-colors"
                title="关闭"
              >
                <svg class="w-4 h-4 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
          
          <!-- 总进度 -->
          <div class="px-4 py-3 bg-base-elevated">
            <div class="flex items-center justify-between mb-2">
              <span class="text-text-secondary text-sm">{{ statusText }}</span>
              <span class="text-brand-sky font-mono font-bold">{{ totalProgress }}%</span>
            </div>
            <div class="h-1.5 bg-base-elevated rounded-full overflow-hidden">
              <div 
                class="h-full bg-gradient-to-r from-brand-primary to-brand-sky transition-all duration-300"
                :style="{ width: `${totalProgress}%` }"
              ></div>
            </div>
          </div>
          
          <!-- 文件列表 -->
          <div class="max-h-60 overflow-y-auto">
            <div 
              v-for="file in store.supplementaryFiles"
              :key="file.id"
              class="px-4 py-3 border-b border-line-light last:border-b-0"
            >
              <div class="flex items-start gap-3">
                <div class="text-lg">{{ getFileIcon(file.type) }}</div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center justify-between">
                    <span class="text-text-primary text-sm truncate">{{ file.name }}</span>
                    <span :class="getStatusClass(file.status)" class="text-xs ml-2 flex-shrink-0">
                      <span v-if="file.status === 'completed'">完成</span>
                      <span v-else-if="file.status === 'uploading'">{{ file.progress }}%</span>
                      <span v-else-if="file.status === 'error'">失败</span>
                      <span v-else>等待中</span>
                    </span>
                  </div>
                  <div class="flex items-center justify-between mt-1">
                    <span class="text-text-secondary text-xs">{{ getTypeName(file.type) }} · {{ formatFileSize(file.size) }}</span>
                    <div class="flex items-center gap-1">
                      <button 
                        v-if="file.status === 'error'"
                        @click="retryUpload(file.id)"
                        class="p-1 hover:bg-base-elevated rounded transition-colors"
                        title="重试"
                      >
                        <svg class="w-3.5 h-3.5 text-accent-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                      </button>
                      <button 
                        v-if="file.status === 'uploading' || file.status === 'pending'"
                        @click="cancelUpload(file.id)"
                        class="p-1 hover:bg-base-elevated rounded transition-colors"
                        title="取消"
                      >
                        <svg class="w-3.5 h-3.5 text-white/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  </div>
                  
                  <!-- 单文件进度条 -->
                  <div
                    v-if="file.status === 'uploading'"
                    class="mt-2 h-1 bg-base-elevated rounded-full overflow-hidden"
                  >
                    <div 
                      class="h-full bg-brand-primary transition-all duration-300"
                      :style="{ width: `${file.progress}%` }"
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 数据来源显示 -->
          <div v-if="store.selectedDataSource" class="px-4 py-2 bg-base-elevated border-t border-line-light">
            <div class="flex items-center gap-2 text-xs text-text-secondary">
              <span>数据来源:</span>
              <span class="text-text-secondary">{{ store.selectedDataSource }}</span>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<style scoped>
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

/* 自定义滚动条 */
.max-h-60::-webkit-scrollbar {
  width: 4px;
}

.max-h-60::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
}

.max-h-60::-webkit-scrollbar-thumb {
  background: rgba(16, 35, 117, 0.3);
  border-radius: 2px;
}

.max-h-60::-webkit-scrollbar-thumb:hover {
  background: rgba(16, 35, 117, 0.5);
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
</style>

