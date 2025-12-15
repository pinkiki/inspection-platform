<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore, PROCESSING_STAGES, STAGE_NAMES, ESTIMATED_TIME, SUPPLEMENTARY_DISCOUNTS, DATA_SOURCES } from '../stores/project'
import CreditsDisplay from '../components/CreditsDisplay.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import BasicReportPreview from '../components/BasicReportPreview.vue'

const router = useRouter()
const store = useProjectStore()

const showInsufficientCreditsDialog = ref(false)
const processingIntervals = ref([])
const isAdminMode = ref(localStorage.getItem('adminMode') === 'true')

// 额外资料类型映射
const supplementaryTypeNames = {
  pos: 'PoS/轨迹信息',
  sfm: 'SfM结果',
  ortho: '正射影像图',
  model3d: '三维模型'
}

const supplementaryTypeIcons = {
  pos: '📍',
  sfm: '📊',
  ortho: '🗺️',
  model3d: '🏛️'
}

// 模拟问题点位数据
const issuePoints = computed(() => {
  return store.detectionResults
    .filter(r => r.issues.length > 0)
    .map(r => ({
      ...r,
      x: 10 + Math.random() * 80,
      y: 10 + Math.random() * 80
    }))
})

// 当前处理阶段列表（根据模板类型，考虑已上传的额外资料）
const processingStages = computed(() => {
  let stages = [
    PROCESSING_STAGES.AERIAL_TRIANGULATION,
    PROCESSING_STAGES.DENSE_MATCHING,
    PROCESSING_STAGES.DEM_GENERATION
  ]
  
  if (store.selectedTemplate?.includeOrtho) {
    stages.push(PROCESSING_STAGES.ORTHO_GENERATION)
  }
  
  if (store.selectedTemplate?.include3D) {
    stages.push(PROCESSING_STAGES.MODEL_3D_RECONSTRUCTION)
    stages.push(PROCESSING_STAGES.TEXTURE_MAPPING)
  }
  
  // 根据已上传的额外资料跳过某些阶段
  const skippedStages = store.skippedStages
  if (skippedStages.length > 0) {
    stages = stages.filter(stage => !skippedStages.includes(stage))
  }
  
  return stages
})

// 获取被跳过的阶段名称列表
const skippedStageNames = computed(() => {
  return store.skippedStages.map(stage => STAGE_NAMES[stage] || stage)
})

// 已上传的额外资料（已完成的）
const uploadedSupplementary = computed(() => {
  return store.supplementaryFiles.filter(f => f.status === 'completed')
})

// 获取数据来源名称
const dataSourceName = computed(() => {
  if (!store.selectedDataSource) return null
  return DATA_SOURCES[store.selectedDataSource]?.name || store.selectedDataSource
})

// 当前处理的阶段索引
const currentStageIndex = computed(() => {
  const currentStage = store.advancedProcessingStage
  if (currentStage === PROCESSING_STAGES.IDLE) return -1
  if (currentStage === PROCESSING_STAGES.COMPLETED) return processingStages.value.length
  return processingStages.value.indexOf(currentStage)
})

// 获取预计完成时间
const getEstimatedTime = () => {
  const templateId = store.selectedTemplate?.id
  if (!templateId) return null
  
  const estimateKey = templateId === 'ortho' ? 'ortho' : 
                      templateId === '3d' ? '3d' : 
                      templateId === 'full' ? 'full' : null
  
  if (!estimateKey) return null
  
  const estimate = ESTIMATED_TIME[estimateKey]
  const hours = (estimate.min + estimate.max) / 2
  
  const now = new Date()
  const completionTime = new Date(now.getTime() + hours * 60 * 60 * 1000)
  
  return {
    text: `${estimate.min}-${estimate.max}小时`,
    date: completionTime.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }
}

// 处理阶段状态
const getStageStatus = (stage) => {
  const index = processingStages.value.indexOf(stage)
  if (index < currentStageIndex.value) return 'completed'
  if (index === currentStageIndex.value) return 'processing'
  return 'pending'
}

// 切换管理员模式
const toggleAdminMode = () => {
  isAdminMode.value = !isAdminMode.value
  localStorage.setItem('adminMode', isAdminMode.value ? 'true' : 'false')
}

// 管理员：跳过当前阶段
const skipCurrentStage = () => {
  const currentIndex = currentStageIndex.value
  if (currentIndex >= 0 && currentIndex < processingStages.value.length) {
    // 完成当前阶段
    store.setStageProgress(processingStages.value[currentIndex], 100)
    
    // 进入下一阶段或完成
    if (currentIndex + 1 < processingStages.value.length) {
      store.setProcessingStage(processingStages.value[currentIndex + 1])
      store.setStageProgress(processingStages.value[currentIndex + 1], 0)
    } else {
      completeProcessing()
    }
  }
}

// 管理员：快速完成所有阶段
const fastComplete = () => {
  // 完成所有阶段
  processingStages.value.forEach(stage => {
    store.setStageProgress(stage, 100)
  })
  completeProcessing()
}

// 完成处理
const completeProcessing = () => {
  // 清除所有定时器
  processingIntervals.value.forEach(interval => clearInterval(interval))
  processingIntervals.value = []
  
  store.setProcessingStage(PROCESSING_STAGES.COMPLETED)
  store.setAdvancedProcessed(true)
  
  store.setAdvancedData({
    orthoGenerated: store.selectedTemplate?.includeOrtho || false,
    model3DGenerated: store.selectedTemplate?.include3D || false,
    issuePoints: issuePoints.value
  })
}

// 开始处理
const startProcessing = async () => {
  console.log('开始新的处理任务')
  console.log('处理阶段列表:', processingStages.value)
  
  // 计算并保存预计完成时间
  const estimated = getEstimatedTime()
  if (estimated) {
    store.setEstimatedTime(new Date(Date.now() + 4 * 60 * 60 * 1000).toISOString())
  }
  
  // 从第一个阶段开始
  const firstStage = processingStages.value[0]
  console.log('设置第一个阶段:', firstStage)
  store.setProcessingStage(firstStage)
  store.setStageProgress(firstStage, 0)
  
  // 启动处理循环
  processStages()
}

// 恢复处理
const resumeProcessing = () => {
  console.log('恢复处理，当前阶段:', store.advancedProcessingStage)
  console.log('当前进度:', store.getCurrentStageProgress())
  
  if (store.advancedProcessingStage === PROCESSING_STAGES.COMPLETED) {
    console.log('处理已完成，无需恢复')
    return
  }
  
  // 继续当前阶段的处理
  processStages()
}

// 处理各个阶段
const processStages = () => {
  console.log('开始处理阶段，当前阶段:', store.advancedProcessingStage)
  
  const interval = setInterval(() => {
    const currentStage = store.advancedProcessingStage
    
    if (currentStage === PROCESSING_STAGES.COMPLETED) {
      clearInterval(interval)
      return
    }
    
    if (currentStage === PROCESSING_STAGES.IDLE) {
      console.log('当前阶段为IDLE，跳过')
      return
    }
    
    const currentProgress = store.getCurrentStageProgress()
    console.log(`当前阶段: ${currentStage}, 进度: ${currentProgress}%`)
    
    // 每次增加较大的随机进度（加快演示速度）
    const increment = Math.random() * 8 + 4  // 4-12%
    const newProgress = Math.min(100, currentProgress + increment)
    
    store.setStageProgress(currentStage, newProgress)
    console.log(`更新进度到: ${newProgress}%`)
    
    // 当前阶段完成
    if (newProgress >= 100) {
      const currentIndex = processingStages.value.indexOf(currentStage)
      console.log(`阶段 ${currentStage} 完成，当前索引: ${currentIndex}`)
      
      // 进入下一阶段
      if (currentIndex + 1 < processingStages.value.length) {
        const nextStage = processingStages.value[currentIndex + 1]
        console.log(`进入下一阶段: ${nextStage}`)
        store.setProcessingStage(nextStage)
        store.setStageProgress(nextStage, 0)
      } else {
        // 所有阶段完成
        console.log('所有阶段完成')
        clearInterval(interval)
        completeProcessing()
      }
    }
  }, 200) // 每200ms更新一次
  
  processingIntervals.value.push(interval)
  console.log('处理定时器已启动，ID:', interval)
}

onMounted(async () => {
  if (!store.selectedTemplate) {
    router.push('/template')
    return
  }
  
  // 计算需要扣除的积分
  const templateCredits = store.getTemplateCredits(store.selectedTemplate.id)
  const requiredCredits = store.isAdvancedProcessed 
    ? Math.max(0, templateCredits - store.paidTemplateCredits)
    : templateCredits
  
  // 检查积分是否足够
  if (requiredCredits > 0 && !store.canAfford(requiredCredits)) {
    showInsufficientCreditsDialog.value = true
    return
  }
  
  // 扣除积分（如果需要）
  if (requiredCredits > 0) {
    const reason = store.isAdvancedProcessed 
      ? `升级到${store.selectedTemplate.name}` 
      : `生成${store.selectedTemplate.name}`
    
    store.deductCredits(requiredCredits, reason)
    store.setPaidTemplateCredits(templateCredits)
  }
  
  // 检查处理状态
  if (store.advancedProcessingStage && 
      store.advancedProcessingStage !== PROCESSING_STAGES.IDLE &&
      store.advancedProcessingStage !== PROCESSING_STAGES.COMPLETED) {
    // 恢复处理
    resumeProcessing()
  } else if (store.advancedProcessingStage === PROCESSING_STAGES.COMPLETED) {
    // 已完成，不需要处理
  } else {
    // 开始新的处理
    startProcessing()
  }
})

onBeforeUnmount(() => {
  // 清除所有定时器
  processingIntervals.value.forEach(interval => clearInterval(interval))
  processingIntervals.value = []
})

// 积分不足返回
const handleInsufficientCredits = () => {
  showInsufficientCreditsDialog.value = false
  router.push('/template')
}

// 下一步
const goNext = () => {
  store.setCurrentStep(6)
  router.push('/export')
}


// 处理基础报告下载 - 跳转到导出页面
const handleDownloadBasic = () => {
  store.setCurrentStep(6)
  router.push('/export')
}

// 获取状态颜色
const getStatusColor = (status) => {
  switch (status) {
    case 'danger': return '#102375'
    case 'warning': return '#4e66cc'
    case 'success': return '#6fbcce'
    default: return '#6fbcce'
  }
}
</script>

<template>
  <div class="animate-fade-in">
    <!-- 标题和积分显示 -->
    <div class="flex items-start justify-between mb-8">
      <div class="text-center flex-1">
        <h1 class="text-3xl font-bold text-text-primary mb-2">进阶报告生成</h1>
        <p class="text-text-secondary">
          <span v-if="store.selectedTemplate?.includeOrtho">正射影像</span>
          <span v-if="store.selectedTemplate?.includeOrtho && store.selectedTemplate?.include3D"> + </span>
          <span v-if="store.selectedTemplate?.include3D">三维模型</span>
          处理中，请耐心等待
        </p>
      </div>
      <div class="flex items-center gap-3">
        <!-- 管理员模式切换 -->
        <button
          @click="toggleAdminMode"
          class="px-3 py-2 rounded-lg text-xs transition-colors"
          :class="isAdminMode ? 'bg-accent-warning/20 text-accent-warning' : 'bg-base-elevated text-muted'"
          title="切换管理员模式"
        >
          {{ isAdminMode ? '🔧 管理员' : '👤 普通' }}
        </button>
        <CreditsDisplay />
      </div>
    </div>
    
    <!-- 处理中状态 -->
    <div v-if="store.advancedProcessingStage !== PROCESSING_STAGES.COMPLETED">
      <!-- 已上传的额外资料提示 -->
      <div v-if="uploadedSupplementary.length > 0" class="glass-card p-4 mb-6 bg-accent-success/10 border border-accent-success/30">
        <div class="flex items-start justify-between">
          <div class="flex items-start gap-3">
            <div class="w-10 h-10 rounded-full bg-accent-success/20 flex items-center justify-center flex-shrink-0">
              <svg class="w-5 h-5 text-accent-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div>
              <div class="text-accent-success font-semibold mb-1">已上传额外处理资料</div>
              <div class="flex flex-wrap gap-2 mb-2">
                <span
                  v-for="file in uploadedSupplementary"
                  :key="file.id"
                  class="inline-flex items-center gap-1 px-2 py-1 bg-base-elevated rounded text-xs text-text-primary"
                >
                  <span>{{ supplementaryTypeIcons[file.type] }}</span>
                  <span>{{ supplementaryTypeNames[file.type] }}</span>
                </span>
              </div>
              <div class="text-muted text-xs">
                数据来源：{{ dataSourceName }}
                <span v-if="skippedStageNames.length > 0" class="ml-2">
                  · 已跳过：{{ skippedStageNames.join('、') }}
                </span>
              </div>
            </div>
          </div>
          <div class="text-right">
            <div class="text-accent-success text-lg font-bold">节省 {{ store.supplementaryDiscount }}%</div>
            <div class="text-muted text-xs">积分优惠</div>
          </div>
        </div>
      </div>
      
      <!-- 预计时间和二维码 -->
      <div class="grid grid-cols-3 gap-6 mb-6">
        <!-- 二维码区域 -->
        <div class="glass-card p-6 text-center">
          <div class="mb-4">
            <div class="w-40 h-40 mx-auto bg-white rounded-lg flex items-center justify-center">
              <div class="text-center">
                <div class="text-4xl mb-2">📱</div>
                <div class="text-sm text-gray-600">二维码占位</div>
                <div class="text-xs text-gray-400 mt-1">扫描关注公众号</div>
              </div>
            </div>
          </div>
          <p class="text-text-secondary text-sm">扫描关注公众号</p>
          <p class="text-muted text-xs mt-1">任务完成后将发送通知</p>
        </div>

        <!-- 处理阶段进度 -->
        <div class="glass-card p-6 col-span-2">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-text-primary">处理进度</h3>
            <div v-if="getEstimatedTime()" class="text-sm text-text-secondary">
              预计完成：{{ getEstimatedTime().date }}
              <span class="text-brand-sky ml-2">({{ getEstimatedTime().text }})</span>
            </div>
          </div>
          
          <div class="space-y-3">
            <div 
              v-for="stage in processingStages"
              :key="stage"
              class="flex items-center gap-3"
            >
              <!-- 状态图标 -->
              <div class="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center"
                :class="{
                  'bg-accent-success text-white': getStageStatus(stage) === 'completed',
                  'bg-brand-primary text-white': getStageStatus(stage) === 'processing',
                  'bg-base-elevated text-text-secondary': getStageStatus(stage) === 'pending'
                }"
              >
                <svg v-if="getStageStatus(stage) === 'completed'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
                <svg v-else-if="getStageStatus(stage) === 'processing'" class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <div v-else class="w-2 h-2 rounded-full bg-current"></div>
              </div>
              
              <!-- 阶段名称 -->
              <div class="flex-1">
                <div class="flex items-center justify-between">
                  <span 
                    class="text-sm font-medium"
                    :class="{
                      'text-text-primary': getStageStatus(stage) !== 'pending',
                      'text-text-secondary': getStageStatus(stage) === 'pending'
                    }"
                  >
                    {{ STAGE_NAMES[stage] }}
                  </span>
                  <span 
                    v-if="getStageStatus(stage) === 'processing'"
                    class="text-sm font-mono text-brand-sky"
                  >
                    {{ Math.round(store.advancedProcessingProgress[stage]) }}%
                  </span>
                </div>
                
                <!-- 进度条（仅处理中显示） -->
                <div 
                  v-if="getStageStatus(stage) === 'processing'"
                  class="mt-1 h-1.5 bg-base-elevated rounded-full overflow-hidden"
                >
                  <div 
                    class="h-full bg-gradient-to-r from-brand-primary to-brand-sky transition-all duration-300"
                    :style="{ width: `${store.advancedProcessingProgress[stage]}%` }"
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 管理员调试面板 -->
      <div v-if="isAdminMode" class="glass-card p-4 mb-6 bg-accent-warning/10 border border-accent-warning/30">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-accent-warning font-semibold flex items-center gap-2 mb-1">
              <span>🔧</span>
              <span>管理员调试工具</span>
            </div>
            <div class="text-text-secondary text-sm">
              当前阶段：{{ STAGE_NAMES[store.advancedProcessingStage] || '空闲' }}
              ({{ Math.round(store.getCurrentStageProgress()) }}%)
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button 
              @click="skipCurrentStage"
              :disabled="currentStageIndex < 0 || currentStageIndex >= processingStages.length"
              class="px-4 py-2 rounded-lg bg-accent-warning/20 hover:bg-accent-warning/30 text-accent-warning text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              跳过当前阶段
            </button>
            <button 
              @click="fastComplete"
              class="px-4 py-2 rounded-lg bg-accent-success/20 hover:bg-accent-success/30 text-accent-success text-sm transition-colors"
            >
              快速完成
            </button>
          </div>
        </div>
      </div>
      
      <!-- 基础报告预览 -->
      <div class="glass-card p-6">
        <BasicReportPreview @download-basic="handleDownloadBasic" />
      </div>
    </div>
    
    <!-- 处理完成状态 -->
    <div v-else>
      <!-- 问题统计 -->
      <div class="glass-card p-6 mb-6">
        <h3 class="text-lg font-semibold text-text-primary mb-4">问题点位统计</h3>
        <div class="grid grid-cols-4 gap-4">
          <div class="text-center p-4 rounded-xl bg-base-elevated">
            <div class="text-3xl font-bold text-text-primary">{{ issuePoints.length }}</div>
            <div class="text-sm text-text-secondary">问题点位</div>
          </div>
          <div class="text-center p-4 rounded-xl bg-accent-danger/10">
            <div class="text-3xl font-bold text-accent-danger">
              {{ issuePoints.filter(p => p.status === 'danger').length }}
            </div>
            <div class="text-sm text-text-secondary">严重问题</div>
          </div>
          <div class="text-center p-4 rounded-xl bg-accent-warning/10">
            <div class="text-3xl font-bold text-accent-warning">
              {{ issuePoints.filter(p => p.status === 'warning').length }}
            </div>
            <div class="text-sm text-text-secondary">一般问题</div>
          </div>
          <div class="text-center p-4 rounded-xl bg-brand-cyan/10">
            <div class="text-3xl font-bold text-brand-cyan">
              {{ store.detectionResults.reduce((sum, r) => sum + r.issues.length, 0) }}
            </div>
            <div class="text-sm text-text-secondary">问题总数</div>
          </div>
        </div>
      </div>
      
      <!-- 已上传的额外资料信息（完成状态） -->
      <div v-if="uploadedSupplementary.length > 0" class="glass-card p-4 mb-6 bg-accent-success/10 border border-accent-success/30">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <svg class="w-5 h-5 text-accent-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <span class="text-text-primary text-sm">使用了您上传的额外资料</span>
              <span class="text-text-secondary text-xs ml-2">
                ({{ uploadedSupplementary.map(f => supplementaryTypeNames[f.type]).join('、') }})
              </span>
            </div>
          </div>
          <div class="text-accent-success font-bold">节省了 {{ store.supplementaryDiscount }}% 积分</div>
        </div>
      </div>
      
      <!-- 成功提示 -->
      <div class="glass-card p-8 mb-6 text-center">
        <div class="text-6xl mb-4">✅</div>
        <h3 class="text-2xl font-bold text-text-primary mb-2">进阶报告生成完成！</h3>
        <p class="text-text-secondary">所有处理阶段已完成，您可以继续导出报告</p>
      </div>
      
      <!-- 操作按钮 -->
      <div class="flex justify-end">
        <button @click="goNext" class="btn-primary">
          导出报告
          <svg class="w-5 h-5 ml-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
          </svg>
        </button>
      </div>
    </div>
    
    <!-- 积分不足对话框 -->
    <ConfirmDialog
      :show="showInsufficientCreditsDialog"
      title="积分不足"
      message="您的积分不足以生成此报告，请返回选择其他模板或充值积分。"
      :credits-cost="0"
      confirm-text="返回模板选择"
      :cancel-text="null"
      type="danger"
      @confirm="handleInsufficientCredits"
      @close="handleInsufficientCredits"
    />
  </div>
</template>

<style scoped>
@keyframes spin {
  to { transform: rotate(360deg); }
}

.animate-spin {
  animation: spin 1s linear infinite;
}
</style>