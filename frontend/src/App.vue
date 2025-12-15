<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { RouterView, useRouter } from 'vue-router'
import AppHeader from './components/AppHeader.vue'
import StepProgress from './components/StepProgress.vue'
import UploadProgressFloat from './components/UploadProgressFloat.vue'
import { useProjectStore } from './stores/project'

const router = useRouter()
const store = useProjectStore()

const showRecoveryModal = ref(false)

// 处理页面离开前提示
const handleBeforeUnload = (e) => {
  if (store.hasUnsavedData) {
    e.preventDefault()
    e.returnValue = '您有未完成的项目，确定要离开吗？'
    return e.returnValue
  }
}

// 检查是否有未完成的项目
const checkUnfinishedProject = () => {
  if (store.projectId && !store.isProjectCompleted && store.currentStep > 1) {
    showRecoveryModal.value = true
  }
}

// 继续之前的项目
const continueProject = () => {
  showRecoveryModal.value = false
  // 根据当前步骤跳转到对应页面
  const stepRoutes = {
    1: '/',
    2: '/analysis',
    3: '/template',
    4: '/review',
    5: '/advanced',
    6: '/export'
  }
  const route = stepRoutes[store.currentStep] || '/'
  router.push(route)
}

// 开始新项目
const startNewProject = () => {
  store.resetProject()
  showRecoveryModal.value = false
  router.push('/')
}

onMounted(() => {
  window.addEventListener('beforeunload', handleBeforeUnload)
  // 延迟检查，等待路由初始化
  setTimeout(checkUnfinishedProject, 100)
})

onUnmounted(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
})
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <!-- 顶部导航 -->
    <AppHeader />
    
    <!-- 步骤进度指示器 -->
    <StepProgress />
    
    <!-- 主内容区域 -->
    <main class="flex-1 container mx-auto px-6 py-8">
      <RouterView v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </RouterView>
    </main>
    
    <!-- 页脚 -->
    <footer class="footer-bar">
      <div class="container mx-auto px-6 text-center">
        <span class="text-brand-muted text-xs">© 2024 智巡 AI无人机巡检平台</span>
        <span class="text-brand-muted/50 text-xs mx-2">|</span>
        <span class="text-brand-muted/50 text-xs">Powered by ZeemoTech</span>
      </div>
    </footer>
    
    <!-- 全局上传进度浮窗 -->
    <UploadProgressFloat />
    
    <!-- 项目恢复弹窗 -->
    <Teleport to="body">
      <div 
        v-if="showRecoveryModal"
        class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-8"
      >
        <div class="glass-card p-8 max-w-md w-full text-center animate-fade-in">
          <div class="modal-icon">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          
          <h3 class="text-lg font-bold text-text-primary mb-2">发现未完成的项目</h3>
          <p class="text-brand-muted text-sm mb-2">
            项目ID: <span class="text-brand-primary font-mono font-bold">{{ store.projectId }}</span>
          </p>
          <p class="text-brand-muted/70 text-xs mb-6">
            上次进行到第 {{ store.currentStep }} 步，共 {{ store.uploadedImages.length }} 张图片
          </p>
          
          <div class="flex gap-4">
            <button 
              @click="startNewProject"
              class="flex-1 btn-secondary"
            >
              开始新项目
            </button>
            <button 
              @click="continueProject"
              class="flex-1 btn-primary"
            >
              继续处理
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.footer-bar {
  border-top: 1px solid var(--line-light);
  padding: 14px 0;
  background: rgba(255,255,255,0.9);
}

.modal-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 24px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(16,35,117,0.1), rgba(115,162,243,0.1));
  border: 1px solid rgba(16,35,117,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--brand);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
