<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore, CREDIT_PRICES } from '../stores/project'
import ImageAnnotator from '../components/ImageAnnotator.vue'
import CreditsDisplay from '../components/CreditsDisplay.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'

const router = useRouter()
const store = useProjectStore()
const showReanalysisConfirm = ref(false)

const isDetecting = ref(true)
const detectProgress = ref(0)
const selectedImage = ref(null)
const filterStatus = ref('all')
const isEditMode = ref(false)

// 图片预览相关
const previewImageRef = ref(null)
const previewContainerRef = ref(null)
const imageDisplayInfo = ref({ offsetX: 0, offsetY: 0, width: 0, height: 0 })

// 问题列表折叠状态
const expandedIssues = ref(new Set())

// 模拟检测结果
const mockDetectionResults = () => {
  return store.uploadedImages.map((img, index) => {
    const hasIssue = Math.random() > 0.3
    const confidence = 0.7 + Math.random() * 0.25
    
    let issues = []
    if (hasIssue) {
      const issueTypes = [
        { type: 'crack', name: '裂缝', severity: 'danger', description: '检测到长度约15cm的横向裂缝' },
        { type: 'stain', name: '污渍', severity: 'warning', description: '存在明显的水渍痕迹' },
        { type: 'damage', name: '破损', severity: 'danger', description: '局部区域存在明显破损' },
        { type: 'corrosion', name: '锈蚀', severity: 'warning', description: '金属部件出现轻微锈蚀' },
        { type: 'deformation', name: '变形', severity: 'caution', description: '检测到轻微形变' }
      ]
      
      const numIssues = Math.floor(Math.random() * 3) + 1
      for (let i = 0; i < numIssues; i++) {
        const issue = issueTypes[Math.floor(Math.random() * issueTypes.length)]
        issues.push({
          ...issue,
          id: `issue-${index}-${i}`,
          bbox: {
            x: Math.random() * 60 + 10,
            y: Math.random() * 60 + 10,
            width: Math.random() * 20 + 10,
            height: Math.random() * 20 + 10
          },
          confidence: 0.6 + Math.random() * 0.35
        })
      }
    }
    
    return {
      ...img,
      confidence,
      issues,
      status: hasIssue ? (issues.some(i => i.severity === 'danger') ? 'danger' : 'warning') : 'success',
      gps: {
        lat: 31.2 + Math.random() * 0.1,
        lng: 121.4 + Math.random() * 0.1
      },
      suggestion: hasIssue ? '建议进一步检查并安排维修' : '状态良好，无需处理'
    }
  })
}

onMounted(async () => {
  if (!store.selectedTemplate) {
    router.push('/template')
    return
  }
  
  // 检查是否已有缓存的检测结果
  if (store.isDataLoaded('detection') && store.detectionResults.length > 0) {
    // 使用缓存数据，直接显示结果
    isDetecting.value = false
    detectProgress.value = 100
  } else {
    // 模拟检测过程
    const interval = setInterval(() => {
      detectProgress.value += Math.random() * 15
      if (detectProgress.value >= 100) {
        detectProgress.value = 100
        clearInterval(interval)
        
        // 生成模拟检测结果
        const results = mockDetectionResults()
        store.setDetectionResults(results)
        isDetecting.value = false
      }
    }, 200)
  }
  
  // 添加键盘事件监听
  window.addEventListener('keydown', handleKeydown)
  // 添加窗口大小变化监听
  window.addEventListener('resize', updateImageDisplayInfo)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('resize', updateImageDisplayInfo)
})

// 过滤后的结果
const filteredResults = computed(() => {
  if (filterStatus.value === 'all') {
    return store.detectionResults
  }
  return store.detectionResults.filter(r => r.status === filterStatus.value)
})

// 统计数据
const stats = computed(() => {
  const results = store.detectionResults
  return {
    total: results.length,
    danger: results.filter(r => r.status === 'danger').length,
    warning: results.filter(r => r.status === 'warning').length,
    success: results.filter(r => r.status === 'success').length,
    totalIssues: results.reduce((sum, r) => sum + r.issues.length, 0),
    avgConfidence: results.length > 0 
      ? (results.reduce((sum, r) => sum + r.confidence, 0) / results.length * 100).toFixed(1)
      : 0
  }
})

// 重新检测
const reDetect = () => {
  store.resetDataLoadedFlag('detection')
  isDetecting.value = true
  detectProgress.value = 0
  
  const interval = setInterval(() => {
    detectProgress.value += Math.random() * 15
    if (detectProgress.value >= 100) {
      detectProgress.value = 100
      clearInterval(interval)
      
      const results = mockDetectionResults()
      store.setDetectionResults(results)
      isDetecting.value = false
    }
  }, 200)
}

// 选择图片查看详情
const viewDetail = (result) => {
  selectedImage.value = { ...result }
  isEditMode.value = false
  expandedIssues.value = new Set() // 重置折叠状态
}

const closeDetail = () => {
  selectedImage.value = null
  isEditMode.value = false
}

// 进入编辑模式
const enterEditMode = () => {
  isEditMode.value = true
}

// 保存编辑结果
const saveAnnotations = (updatedIssues) => {
  if (selectedImage.value) {
    // 更新检测结果
    const newStatus = updatedIssues.length === 0 
      ? 'success' 
      : (updatedIssues.some(i => i.severity === 'danger') ? 'danger' : 'warning')
    
    const newSuggestion = updatedIssues.length === 0 
      ? '状态良好，无需处理' 
      : '建议进一步检查并安排维修'
    
    store.updateDetectionResultById(selectedImage.value.id, {
      issues: updatedIssues,
      status: newStatus,
      suggestion: newSuggestion
    })
    
    // 更新当前选中的图片
    selectedImage.value = {
      ...selectedImage.value,
      issues: updatedIssues,
      status: newStatus,
      suggestion: newSuggestion
    }
    
    isEditMode.value = false
  }
}

// 图片导航逻辑
const currentImageIndex = computed(() => {
  if (!selectedImage.value) return -1
  return filteredResults.value.findIndex(r => r.id === selectedImage.value.id)
})

const canGoPrev = computed(() => currentImageIndex.value > 0)
const canGoNext = computed(() => currentImageIndex.value >= 0 && currentImageIndex.value < filteredResults.value.length - 1)

const goToPrevImage = () => {
  if (canGoPrev.value) {
    const prevImage = filteredResults.value[currentImageIndex.value - 1]
    // 从store中获取最新数据，确保包含任何已保存的修改
    const latestData = store.detectionResults.find(r => r.id === prevImage.id)
    selectedImage.value = { ...(latestData || prevImage) }
    isEditMode.value = false
  }
}

const goToNextImage = () => {
  if (canGoNext.value) {
    const nextImage = filteredResults.value[currentImageIndex.value + 1]
    // 从store中获取最新数据，确保包含任何已保存的修改
    const latestData = store.detectionResults.find(r => r.id === nextImage.id)
    selectedImage.value = { ...(latestData || nextImage) }
    isEditMode.value = false
  }
}

// 键盘快捷键支持
const handleKeydown = (e) => {
  if (!selectedImage.value) return
  
  if (e.key === 'ArrowLeft') {
    e.preventDefault()
    goToPrevImage()
  } else if (e.key === 'ArrowRight') {
    e.preventDefault()
    goToNextImage()
  } else if (e.key === 'Escape') {
    e.preventDefault()
    closeDetail()
  }
}

// 计算图片实际显示区域
const updateImageDisplayInfo = () => {
  const img = previewImageRef.value
  const container = previewContainerRef.value
  if (!img || !container) return
  
  const containerWidth = container.clientWidth
  const containerHeight = container.clientHeight
  const imgAspect = img.naturalWidth / img.naturalHeight
  const containerAspect = containerWidth / containerHeight
  
  if (imgAspect > containerAspect) {
    // 图片宽度占满容器
    imageDisplayInfo.value.width = containerWidth
    imageDisplayInfo.value.height = containerWidth / imgAspect
    imageDisplayInfo.value.offsetX = 0
    imageDisplayInfo.value.offsetY = (containerHeight - imageDisplayInfo.value.height) / 2
  } else {
    // 图片高度占满容器
    imageDisplayInfo.value.height = containerHeight
    imageDisplayInfo.value.width = containerHeight * imgAspect
    imageDisplayInfo.value.offsetY = 0
    imageDisplayInfo.value.offsetX = (containerWidth - imageDisplayInfo.value.width) / 2
  }
}

// 将百分比坐标转换为像素坐标
const getBboxStyle = (bbox) => {
  const { offsetX, offsetY, width, height } = imageDisplayInfo.value
  return {
    left: `${offsetX + (bbox.x / 100) * width}px`,
    top: `${offsetY + (bbox.y / 100) * height}px`,
    width: `${(bbox.width / 100) * width}px`,
    height: `${(bbox.height / 100) * height}px`
  }
}

// 问题折叠/展开切换
const toggleIssue = (issueId) => {
  if (expandedIssues.value.has(issueId)) {
    expandedIssues.value.delete(issueId)
  } else {
    expandedIssues.value.add(issueId)
  }
  // 触发响应式更新
  expandedIssues.value = new Set(expandedIssues.value)
}

// 下一步
const goNext = () => {
  if (store.selectedTemplate?.includeOrtho || store.selectedTemplate?.include3D) {
    store.setCurrentStep(5)
    router.push('/advanced')
  } else {
    store.setCurrentStep(6)
    router.push('/export')
  }
}

// 返回模板选择
const goBackToTemplate = () => {
  router.push('/template')
}

// 返回场景分析 - 显示确认对话框
const goBackToAnalysis = () => {
  showReanalysisConfirm.value = true
}

// 确认返回场景分析
const confirmBackToAnalysis = () => {
  // 扣除积分
  const success = store.deductCredits(CREDIT_PRICES.SCENE_REANALYSIS, '返回重新选择场景')
  
  if (success) {
    // 清除识别结果和进阶处理状态
    store.resetDataLoadedFlag('detection')
    store.resetDataLoadedFlag('analysis')
    store.setDetectionResults([])
    store.setAnalysisResult(null)
    store.setAdvancedProcessed(false)
    store.setPaidTemplateCredits(0)
    
    showReanalysisConfirm.value = false
    router.push('/analysis')
  }
}

// 取消返回场景分析
const cancelBackToAnalysis = () => {
  showReanalysisConfirm.value = false
}

// 获取状态颜色
const getStatusColor = (status) => {
  switch (status) {
    case 'danger': return 'text-accent-danger'
    case 'warning': return 'text-accent-warning'
    case 'success': return 'text-accent-success'
    default: return 'text-white/50'
  }
}

const getStatusBg = (status) => {
  switch (status) {
    case 'danger': return 'bg-accent-danger/20'
    case 'warning': return 'bg-accent-warning/20'
    case 'success': return 'bg-accent-success/20'
    default: return 'bg-white/10'
  }
}
</script>

<template>
  <div class="animate-fade-in">
    <!-- 标题和积分显示 -->
    <div class="flex items-start justify-between mb-8">
      <div class="text-center flex-1">
        <h1 class="text-2xl font-bold text-text-primary mb-2">识别结果审查</h1>
        <p class="text-brand-muted text-sm">查看每张图片的检测结果，可点击图片进行修正</p>
      </div>
      <CreditsDisplay />
    </div>
    
    <!-- 检测中状态 -->
    <div v-if="isDetecting" class="max-w-2xl mx-auto glass-card p-12 text-center">
      <div class="loading-spinner">
        <div class="spinner-ring"></div>
        <div class="spinner-icon">
          <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          </svg>
        </div>
      </div>
      
      <h3 class="text-lg font-semibold text-text-primary mb-2">正在进行AI检测...</h3>
      <p class="text-brand-muted text-sm mb-6">使用 {{ store.analysisResult?.sceneName }} 算法分析图像</p>
      
      <div class="max-w-md mx-auto">
        <div class="flex items-center justify-between mb-2 text-sm">
          <span class="text-brand-muted">检测进度</span>
          <span class="text-brand-primary font-mono font-bold">{{ Math.round(detectProgress) }}%</span>
        </div>
        <div class="progress-bar-detect">
          <div 
            class="progress-fill-detect"
            :style="{ width: `${detectProgress}%` }"
          ></div>
        </div>
      </div>
    </div>
    
    <!-- 检测结果 -->
    <div v-else>
      <!-- 统计面板 -->
      <div class="grid grid-cols-5 gap-4 mb-6">
        <div class="stat-card text-center">
          <div class="stat-value text-text-primary">{{ stats.total }}</div>
          <div class="stat-label">总图片数</div>
        </div>
        <div class="stat-card text-center">
          <div class="stat-value text-accent-danger">{{ stats.danger }}</div>
          <div class="stat-label">严重问题</div>
        </div>
        <div class="stat-card text-center">
          <div class="stat-value text-accent-warning">{{ stats.warning }}</div>
          <div class="stat-label">一般问题</div>
        </div>
        <div class="stat-card text-center">
          <div class="stat-value text-accent-success">{{ stats.success }}</div>
          <div class="stat-label">正常图片</div>
        </div>
        <div class="stat-card text-center">
          <div class="stat-value text-brand-primary">{{ stats.avgConfidence }}%</div>
          <div class="stat-label">平均置信度</div>
        </div>
      </div>
      
      <!-- 筛选器 -->
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-2">
          <span class="text-brand-muted text-sm">筛选：</span>
          <button 
            @click="filterStatus = 'all'"
            class="filter-btn"
            :class="{ 'active': filterStatus === 'all' }"
          >
            全部 ({{ stats.total }})
          </button>
          <button 
            @click="filterStatus = 'danger'"
            class="filter-btn danger"
            :class="{ 'active': filterStatus === 'danger' }"
          >
            严重 ({{ stats.danger }})
          </button>
          <button 
            @click="filterStatus = 'warning'"
            class="filter-btn warning"
            :class="{ 'active': filterStatus === 'warning' }"
          >
            一般 ({{ stats.warning }})
          </button>
          <button 
            @click="filterStatus = 'success'"
            class="filter-btn success"
            :class="{ 'active': filterStatus === 'success' }"
          >
            正常 ({{ stats.success }})
          </button>
        </div>
        
        <!-- 重新检测按钮 -->
        <button @click="reDetect" class="text-brand-primary text-sm hover:underline flex items-center gap-1">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          重新检测
        </button>
      </div>
      
      <!-- 结果列表 -->
      <div class="glass-card p-4 mb-6">
        <div class="grid grid-cols-4 gap-4">
          <div 
            v-for="result in filteredResults"
            :key="result.id"
            @click="viewDetail(result)"
            class="relative rounded-xl overflow-hidden cursor-pointer group"
          >
            <img 
              :src="result.preview_url || result.previewUrl || result.preview" 
              :alt="result.name"
              class="w-full h-32 object-cover transition-transform group-hover:scale-110"
            >
            
            <!-- 状态遮罩 -->
            <div 
              class="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent"
            ></div>
            
            <!-- 状态标签 -->
            <div 
              class="absolute top-2 right-2 w-3 h-3 rounded-full"
              :class="getStatusBg(result.status)"
            >
              <div 
                class="w-full h-full rounded-full animate-ping"
                :class="result.status === 'danger' ? 'bg-accent-danger' : 'bg-transparent'"
              ></div>
            </div>
            
            <!-- 问题数量 -->
            <div class="absolute bottom-2 left-2 right-2 flex items-center justify-between">
              <span class="text-text-primary text-xs truncate">{{ result.name }}</span>
              <span 
                v-if="result.issues.length > 0"
                class="px-2 py-0.5 rounded text-xs"
                :class="getStatusBg(result.status) + ' ' + getStatusColor(result.status)"
              >
                {{ result.issues.length }} 个问题
              </span>
            </div>
            
            <!-- Hover 遮罩 -->
            <div class="absolute inset-0 bg-brand-primary/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
              <span class="text-text-primary text-sm font-medium">点击查看详情</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 操作按钮 -->
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <button @click="goBackToAnalysis" class="btn-secondary">
            <svg class="w-5 h-5 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 17l-5-5m0 0l5-5m-5 5h12" />
            </svg>
            返回场景分析
          </button>
          
          <button @click="goBackToTemplate" class="btn-secondary">
            返回模板选择
          </button>
        </div>
        
        <button @click="goNext" class="btn-primary">
          {{ store.selectedTemplate?.includeOrtho || store.selectedTemplate?.include3D ? '生成进阶报告' : '导出报告' }}
          <svg class="w-5 h-5 ml-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
          </svg>
        </button>
      </div>
    </div>
    
    <!-- 返回场景分析确认对话框 -->
    <ConfirmDialog
      :show="showReanalysisConfirm"
      title="重新选择场景"
      message="重新选择场景将消耗积分，之前的识别结果将被清除。&#10;&#10;是否确认返回场景分析？"
      :credits-cost="CREDIT_PRICES.SCENE_REANALYSIS"
      confirm-text="确认返回"
      cancel-text="取消"
      type="warning"
      @confirm="confirmBackToAnalysis"
      @cancel="cancelBackToAnalysis"
      @close="cancelBackToAnalysis"
    />
    
    <!-- 详情/编辑弹窗 -->
    <Teleport to="body">
      <div 
        v-if="selectedImage"
        class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-8"
        @click="closeDetail"
      >
        <div 
          class="glass-card p-6 max-w-5xl w-full max-h-[90vh] overflow-auto"
          @click.stop
        >
          <div class="flex items-center justify-between mb-6">
            <div class="flex items-center gap-3">
              <h3 class="text-xl font-bold text-text-primary">
                {{ selectedImage.name }}
              </h3>
              <span class="text-sm text-text-secondary">
                ({{ currentImageIndex + 1 }} / {{ filteredResults.length }})
              </span>
              <span v-if="isEditMode" class="text-brand-sky text-sm">（编辑模式）</span>
            </div>
            <button @click="closeDetail" class="text-text-secondary hover:text-text-primary">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          <!-- 编辑模式 -->
          <div v-if="isEditMode">
            <ImageAnnotator 
              :image-src="selectedImage.preview_url || selectedImage.previewUrl || selectedImage.preview"
              :issues="selectedImage.issues"
              @save="saveAnnotations"
              @cancel="isEditMode = false"
            />
          </div>
          
          <!-- 查看模式 -->
          <div v-else class="grid grid-cols-2 gap-6">
            <!-- 图片预览 -->
            <div 
              ref="previewContainerRef"
              class="relative group flex items-center justify-center bg-black/20 rounded-xl"
              style="min-height: 400px; max-height: 600px;"
            >
              <img 
                ref="previewImageRef"
                :src="selectedImage.preview_url || selectedImage.previewUrl || selectedImage.preview" 
                :alt="selectedImage.name"
                class="max-w-full max-h-full block rounded-xl"
                style="object-fit: contain;"
                @load="updateImageDisplayInfo"
              >
              <!-- 标注框 -->
              <div 
                v-for="issue in selectedImage.issues"
                :key="issue.id"
                class="absolute border-2 rounded pointer-events-none"
                :class="{
                  'border-accent-danger': issue.severity === 'danger',
                  'border-accent-warning': issue.severity === 'warning',
                  'border-accent-caution': issue.severity === 'caution'
                }"
                :style="getBboxStyle(issue.bbox)"
              >
                <span 
                  class="absolute -top-6 left-0 px-2 py-0.5 text-xs rounded whitespace-nowrap"
                  :class="getStatusBg(issue.severity)"
                >
                  {{ issue.name }}
                </span>
              </div>
              
              <!-- 左右导航按钮 -->
              <button 
                v-if="canGoPrev"
                @click="goToPrevImage"
                class="absolute left-2 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-black/60 backdrop-blur-sm text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:bg-black/80 z-10"
                title="上一张 (←)"
              >
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              
              <button 
                v-if="canGoNext"
                @click="goToNextImage"
                class="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-black/60 backdrop-blur-sm text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:bg-black/80 z-10"
                title="下一张 (→)"
              >
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
            
            <!-- 详情信息 -->
            <div class="space-y-4">
              <!-- 基本信息 -->
              <div class="glass-card p-4">
                <h4 class="text-text-primary font-semibold mb-3">基本信息</h4>
                <div class="space-y-2 text-sm">
                  <div class="flex justify-between">
                    <span class="text-text-secondary">置信度</span>
                    <span class="text-brand-sky">{{ (selectedImage.confidence * 100).toFixed(1) }}%</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-text-secondary">GPS位置</span>
                    <span class="text-text-primary font-mono">{{ selectedImage.gps?.lat?.toFixed(4) }}, {{ selectedImage.gps?.lng?.toFixed(4) }}</span>
                  </div>
                </div>
              </div>
              
              <!-- 问题列表 -->
              <div class="glass-card p-4">
                <h4 class="text-text-primary font-semibold mb-3 sticky top-0 bg-inherit z-10">
                  检测到的问题 ({{ selectedImage.issues.length }})
                </h4>
                <div v-if="selectedImage.issues.length === 0" class="text-accent-success text-sm">
                  未检测到问题，状态良好
                </div>
                <div v-else class="space-y-2 max-h-96 overflow-y-auto">
                  <div 
                    v-for="issue in selectedImage.issues"
                    :key="issue.id"
                    class="rounded-lg overflow-hidden"
                    :class="getStatusBg(issue.severity)"
                  >
                    <!-- 问题标题（始终可见，可点击展开） -->
                    <button 
                      @click="toggleIssue(issue.id)"
                      class="w-full p-3 text-left flex items-center justify-between hover:bg-white/5 transition-colors"
                    >
                      <div class="flex items-center gap-2">
                        <span class="font-medium" :class="getStatusColor(issue.severity)">
                          {{ issue.name }}
                        </span>
                        <span class="text-xs text-text-secondary">
                          {{ (issue.confidence * 100).toFixed(0) }}%
                        </span>
                      </div>
                      <svg 
                        class="w-4 h-4 transition-transform flex-shrink-0"
                        :class="{ 'rotate-180': expandedIssues.has(issue.id) }"
                        fill="none" 
                        stroke="currentColor" 
                        viewBox="0 0 24 24"
                      >
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                    
                    <!-- 问题详情（展开时显示） -->
                    <div 
                      v-if="expandedIssues.has(issue.id)"
                      class="px-3 pb-3"
                    >
                      <p class="text-sm text-text-secondary">{{ issue.description }}</p>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 处理建议 -->
              <div class="glass-card p-4">
                <h4 class="text-text-primary font-semibold mb-2">处理建议</h4>
                <p class="text-text-secondary text-sm">{{ selectedImage.suggestion }}</p>
              </div>
              
              <!-- 操作按钮 -->
              <button @click="enterEditMode" class="btn-primary w-full">
                <svg class="w-4 h-4 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                编辑标注结果
              </button>
            </div>
          </div>
          
          <!-- 快捷键提示 -->
          <div class="mt-4 pt-4 border-t border-line-light text-center text-xs text-text-secondary">
            快捷键：← 上一张 · → 下一张 · ESC 关闭
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.loading-spinner {
  width: 96px;
  height: 96px;
  margin: 0 auto 24px;
  position: relative;
}

.spinner-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 4px solid rgba(16,35,117,0.2);
}

.spinner-ring::after {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  border: 4px solid transparent;
  border-top-color: var(--brand);
  animation: spin 1s linear infinite;
}

.spinner-icon {
  position: absolute;
  inset: 12px;
  border-radius: 50%;
  background: rgba(16,35,117,0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--brand);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 自定义滚动条样式 */
.max-h-96::-webkit-scrollbar {
  width: 6px;
}

.max-h-96::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 3px;
}

.max-h-96::-webkit-scrollbar-thumb {
  background: rgba(16, 35, 117, 0.3);
  border-radius: 3px;
}

.max-h-96::-webkit-scrollbar-thumb:hover {
  background: rgba(16, 35, 117, 0.5);
}

.progress-bar-detect {
  height: 8px;
  background: rgba(245,245,245,0.8);
  border-radius: 999px;
  overflow: hidden;
  border: 1px solid var(--line-light);
}

.progress-fill-detect {
  height: 100%;
  background: linear-gradient(90deg, var(--brand), var(--good));
  border-radius: 999px;
  transition: width 0.3s ease;
}

.filter-btn {
  padding: 8px 14px;
  border-radius: 10px;
  font-size: 13px;
  transition: all 0.18s ease;
  border: 1px solid var(--line);
  background: rgba(255,255,255,0.8);
  color: var(--muted);
}

.filter-btn:hover {
  background: rgba(245,245,245,0.9);
  border-color: rgba(16,35,117,0.25);
  color: var(--text);
}

.filter-btn.active {
  background: rgba(16,35,117,0.1);
  border-color: rgba(16,35,117,0.4);
  color: var(--brand);
}

.filter-btn.danger.active {
  background: rgba(16,35,117,0.1);
  border-color: rgba(16,35,117,0.4);
  color: var(--bad);
}

.filter-btn.warning.active {
  background: rgba(78,102,204,0.1);
  border-color: rgba(78,102,204,0.4);
  color: var(--warn);
}

.filter-btn.success.active {
  background: rgba(111,188,206,0.1);
  border-color: rgba(111,188,206,0.4);
  color: var(--good);
}

.stat-card {
  padding: 16px;
  border-radius: 14px;
  border: 1px solid var(--line-light);
  background: rgba(255,255,255,0.95);
  backdrop-filter: blur(10px);
}

.stat-value {
  font-size: 28px;
  font-weight: 800;
}

.stat-label {
  font-size: 12px;
  color: var(--muted);
  margin-top: 4px;
}
</style>
