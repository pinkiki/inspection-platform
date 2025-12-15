<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore, CREDIT_PRICES } from '../stores/project'
import CreditsDisplay from '../components/CreditsDisplay.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'

const router = useRouter()
const store = useProjectStore()

const isAnalyzing = ref(true)
const analysisProgress = ref(0)
const selectedScene = ref(null)
const isReturning = ref(false)  // 是否从后续步骤返回
const showConfirmDialog = ref(false)
const confirmDialogData = ref({
  title: '',
  message: '',
  creditsCost: 0
})

// 模拟场景类型
const sceneTypes = [
  { 
    id: 'building', 
    name: '建筑外立面', 
    icon: '🏢', 
    confidence: 0.92,
    description: '适用于建筑物外墙、玻璃幕墙的缺陷检测',
    algorithms: ['外墙裂缝检测', '玻璃破损识别', '空鼓检测']
  },
  { 
    id: 'solar', 
    name: '光伏板', 
    icon: '☀️', 
    confidence: 0.85,
    description: '适用于光伏电站的组件缺陷检测',
    algorithms: ['热斑检测', '隐裂识别', '污染分析']
  },
  { 
    id: 'road', 
    name: '道路病害', 
    icon: '🛣️', 
    confidence: 0.78,
    description: '适用于道路路面的病害检测',
    algorithms: ['裂缝检测', '坑洞识别', '车辙分析']
  },
  { 
    id: 'power', 
    name: '电力设施', 
    icon: '⚡', 
    confidence: 0.72,
    description: '适用于输电线路、变电设备的巡检',
    algorithms: ['绝缘子检测', '导线异物', '设备锈蚀']
  }
]

// 模拟分析过程
onMounted(async () => {
  // 检查是否有上传的图片
  if (store.uploadedImages.length === 0) {
    router.push('/')
    return
  }
  
  // 检查是否已有缓存的分析结果
  if (store.isDataLoaded('analysis') && store.analysisResult) {
    // 从后续步骤返回，使用缓存数据
    isAnalyzing.value = false
    analysisProgress.value = 100
    selectedScene.value = store.analysisResult.sceneType
    isReturning.value = true  // 标记为返回状态
    return
  }
  
  // 模拟分析进度
  const interval = setInterval(() => {
    analysisProgress.value += Math.random() * 20
    if (analysisProgress.value >= 100) {
      analysisProgress.value = 100
      clearInterval(interval)
      isAnalyzing.value = false
      // 默认选择置信度最高的
      selectedScene.value = sceneTypes[0].id
    }
  }, 300)
})

// 选择场景
const selectScene = (scene) => {
  selectedScene.value = scene.id
}

// 重新分析
const reAnalyze = () => {
  store.resetDataLoadedFlag('analysis')
  isAnalyzing.value = true
  analysisProgress.value = 0
  selectedScene.value = null
  
  // 重新执行分析
  const interval = setInterval(() => {
    analysisProgress.value += Math.random() * 20
    if (analysisProgress.value >= 100) {
      analysisProgress.value = 100
      clearInterval(interval)
      isAnalyzing.value = false
      selectedScene.value = sceneTypes[0].id
    }
  }, 300)
}

// 下一步 - 显示确认对话框
const goNext = () => {
  if (!selectedScene.value) return
  
  // 检查是否是重新选择场景
  const isReselecting = isReturning.value && selectedScene.value !== store.analysisResult?.sceneType
  
  // 设置确认对话框内容
  if (isReturning.value) {
    if (isReselecting) {
      // 重新选择场景，需要扣除积分
      confirmDialogData.value = {
        title: '重新选择场景',
        message: '重新选择场景将消耗积分，并且之前的识别结果将被清除。',
        creditsCost: CREDIT_PRICES.SCENE_REANALYSIS
      }
    } else {
      // 保持原场景，不扣积分，直接进入下一步
      confirmSceneSelection()
      return
    }
  } else {
    // 首次选择场景，不扣除积分
    confirmDialogData.value = {
      title: '确认场景选择',
      message: '确认选择此场景并进入下一步。',
      creditsCost: 0
    }
  }
  
  showConfirmDialog.value = true
}

// 确认场景选择
const confirmSceneSelection = () => {
  const scene = sceneTypes.find(s => s.id === selectedScene.value)
  const isReselecting = isReturning.value && selectedScene.value !== store.analysisResult?.sceneType
  
  // 扣除积分
  if (confirmDialogData.value.creditsCost > 0) {
    const reason = isReselecting ? '重新选择场景' : '场景分析确认'
    const success = store.deductCredits(confirmDialogData.value.creditsCost, reason)
    
    if (!success) {
      // 积分不足，不应该到这里（对话框已经做了检查）
      showConfirmDialog.value = false
      return
    }
  }
  
  // 如果是重新选择场景，清除之前的数据
  if (isReselecting) {
    store.resetDataLoadedFlag('detection')
    store.setDetectionResults([])
    store.setAdvancedProcessed(false)
    store.setPaidTemplateCredits(0)
  }
  
  // 保存场景分析结果
  store.setAnalysisResult({
    sceneType: scene.id,
    sceneName: scene.name,
    confidence: scene.confidence,
    algorithms: scene.algorithms
  })
  
  showConfirmDialog.value = false
  store.setCurrentStep(3)
  router.push('/template')
}

// 取消确认
const cancelConfirmation = () => {
  showConfirmDialog.value = false
}

// 返回上一步
const goBack = () => {
  router.push('/')
}
</script>

<template>
  <div class="max-w-5xl mx-auto animate-fade-in">
    <!-- 标题和积分显示 -->
    <div class="flex items-start justify-between mb-8">
      <div class="text-center flex-1">
        <h1 class="text-3xl font-bold text-text-primary mb-2">场景分析与算法匹配</h1>
        <p class="text-text-secondary">AI 正在分析您的图像，识别巡检场景并匹配最佳检测算法</p>
      </div>
      <CreditsDisplay />
    </div>
    
    <!-- 分析中状态 -->
    <div v-if="isAnalyzing" class="glass-card p-12 text-center">
      <div class="w-24 h-24 mx-auto mb-6 relative">
        <!-- 旋转动画 -->
        <div class="absolute inset-0 rounded-full border-4 border-brand-primary/20"></div>
        <div class="absolute inset-0 rounded-full border-4 border-transparent border-t-brand-primary animate-spin"></div>
        <div class="absolute inset-3 rounded-full bg-brand-primary/10 flex items-center justify-center">
          <svg class="w-10 h-10 text-brand-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
      </div>
      
      <h3 class="text-xl font-semibold text-text-primary mb-2">正在分析图像特征...</h3>
      <p class="text-text-secondary mb-6">已分析 {{ store.uploadedImages.length }} 张图片</p>

      <!-- 进度条 -->
      <div class="max-w-md mx-auto">
        <div class="flex items-center justify-between mb-2 text-sm">
          <span class="text-text-secondary">分析进度</span>
          <span class="text-brand-sky font-mono">{{ Math.round(analysisProgress) }}%</span>
        </div>
        <div class="h-2 bg-base-elevated rounded-full overflow-hidden">
          <div 
            class="h-full bg-gradient-to-r from-brand-primary to-brand-sky transition-all duration-300"
            :style="{ width: `${analysisProgress}%` }"
          ></div>
        </div>
      </div>
    </div>
    
    <!-- 分析结果 -->
    <div v-else>
      <!-- 识别结果提示 -->
      <div class="glass-card p-6 mb-6 flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-xl bg-accent-success/20 flex items-center justify-center">
            <svg class="w-6 h-6 text-accent-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div>
            <h3 class="text-text-primary font-semibold">分析完成</h3>
            <p class="text-text-secondary text-sm">已识别出可能的场景类型，请确认或手动选择</p>
          </div>
        </div>
        <!-- 重新分析按钮 -->
        <button @click="reAnalyze" class="text-brand-sky text-sm hover:underline flex items-center gap-1">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          重新分析
        </button>
      </div>
      
      <!-- 场景选择卡片 -->
      <div class="grid grid-cols-2 gap-4 mb-8">
        <div 
          v-for="scene in sceneTypes"
          :key="scene.id"
          @click="selectScene(scene)"
          class="glass-card-hover p-6 cursor-pointer relative"
          :class="{
            'ring-2 ring-brand-primary': selectedScene === scene.id
          }"
        >
          <div class="flex items-start justify-between mb-4">
            <div class="text-4xl">{{ scene.icon }}</div>
            <div 
              class="px-3 py-1 rounded-full text-xs font-medium"
              :class="{
                'bg-accent-success/20 text-accent-success': scene.confidence >= 0.9,
                'bg-accent-warning/20 text-accent-warning': scene.confidence >= 0.7 && scene.confidence < 0.9,
                'bg-base-elevated text-text-secondary': scene.confidence < 0.7
              }"
            >
              {{ (scene.confidence * 100).toFixed(0) }}% 匹配
            </div>
          </div>
          
          <h3 class="text-xl font-semibold text-text-primary mb-2">{{ scene.name }}</h3>
          <p class="text-text-secondary text-sm mb-4">{{ scene.description }}</p>
          
          <div class="flex flex-wrap gap-2">
            <span 
              v-for="algo in scene.algorithms" 
              :key="algo"
              class="px-2 py-1 bg-brand-primary/20 text-brand-sky text-xs rounded"
            >
              {{ algo }}
            </span>
          </div>
          
          <!-- 选中指示器 -->
          <div 
            v-if="selectedScene === scene.id"
            class="absolute top-4 right-4 w-6 h-6 rounded-full bg-brand-primary flex items-center justify-center"
          >
            <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
          </div>
        </div>
      </div>
      
      <!-- 操作按钮 -->
      <div class="flex items-center justify-between">
        <button @click="goBack" class="btn-secondary">
          <svg class="w-5 h-5 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 17l-5-5m0 0l5-5m-5 5h12" />
          </svg>
          返回上传
        </button>
        
        <button 
          @click="goNext"
          :disabled="!selectedScene"
          class="btn-primary"
        >
          选择报告模板
          <svg class="w-5 h-5 ml-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
          </svg>
        </button>
      </div>
    </div>
    
    <!-- 确认对话框 -->
    <ConfirmDialog
      :show="showConfirmDialog"
      :title="confirmDialogData.title"
      :message="confirmDialogData.message"
      :credits-cost="confirmDialogData.creditsCost"
      confirm-text="确认"
      cancel-text="取消"
      :type="confirmDialogData.creditsCost > 0 ? 'warning' : 'info'"
      @confirm="confirmSceneSelection"
      @cancel="cancelConfirmation"
      @close="cancelConfirmation"
    />
  </div>
</template>
