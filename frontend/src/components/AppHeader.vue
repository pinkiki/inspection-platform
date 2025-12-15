<script setup>
import { useProjectStore } from '../stores/project'

const store = useProjectStore()
</script>

<template>
  <header class="header-bar">
    <div class="container mx-auto px-6">
      <div class="flex items-center justify-between h-16">
        <!-- Logo -->
        <div class="flex items-center gap-3">
          <div class="logo-icon">
            <span class="logo-text">AI</span>
          </div>
          <div>
            <h1 class="text-base font-bold text-text-primary tracking-wide">智巡</h1>
            <p class="text-xs text-brand-muted">AI无人机巡检平台</p>
          </div>
        </div>
        
        <!-- 项目状态 -->
        <div class="flex items-center gap-4">
          <div v-if="store.projectId" class="status-chip">
            <span class="text-brand-muted">项目ID:</span>
            <span class="text-brand-primary font-mono font-bold">{{ store.projectId }}</span>
          </div>
          
          <div v-if="store.uploadedImages.length > 0" class="status-chip">
            <svg class="w-4 h-4 text-brand-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <span class="text-text-primary">{{ store.uploadedImages.length }} 张图片</span>
          </div>
          
          <!-- 新建项目按钮 -->
          <button 
            @click="store.resetProject()"
            class="btn-small"
          >
            <svg class="w-4 h-4 mr-1.5 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            新建项目
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
.header-bar {
  position: sticky;
  top: 0;
  z-index: 50;
  border-bottom: 1px solid var(--line-light);
  background: rgba(255,255,255,0.9);
  backdrop-filter: blur(10px);
}

.logo-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: #102375;
  box-shadow: 0 4px 12px rgba(16,35,117,0.15);
  display: grid;
  place-items: center;
}

.logo-text {
  font-weight: 800;
  font-size: 14px;
  color: #ffffff;
}

.status-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 10px;
  border: 1px solid var(--line-light);
  background: rgba(245,245,245,0.6);
  font-size: 12px;
}
</style>

