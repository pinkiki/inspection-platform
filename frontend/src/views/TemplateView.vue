<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore, CREDIT_PRICES } from '../stores/project'
import ReportPreviewModal from '../components/ReportPreviewModal.vue'
import CreditsDisplay from '../components/CreditsDisplay.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import SupplementaryUploadModal from '../components/SupplementaryUploadModal.vue'

const router = useRouter()
const store = useProjectStore()

const selectedTemplateId = ref(null)
const previewTemplate = ref(null)
const showConfirmDialog = ref(false)
const switchWarning = ref('')
const showSupplementaryModal = ref(false)

// 报告模板
const templates = [
  {
    id: 'basic',
    name: '基础检测报告',
    description: '包含所有图像的问题检测、描述和处理建议',
    icon: '📋',
    features: ['单张图像问题标注', '问题清单汇总', '处理建议', 'GPS定位信息'],
    includeOrtho: false,
    include3D: false,
    estimatedTime: '5-10 分钟',
    credits: CREDIT_PRICES.TEMPLATE_BASIC
  },
  {
    id: 'ortho',
    name: '正射影像报告',
    description: '在基础报告上增加正射影像图，问题点位映射到正射图上',
    icon: '🗺️',
    features: ['基础报告全部功能', '正射影像生成', '问题点位映射', '区域统计分析'],
    includeOrtho: true,
    include3D: false,
    estimatedTime: '15-30 分钟',
    credits: CREDIT_PRICES.TEMPLATE_ORTHO
  },
  {
    id: '3d',
    name: '三维模型报告',
    description: '生成三维实景模型，问题点位在模型上立体展示',
    icon: '🏗️',
    features: ['基础报告全部功能', '三维模型重建', '问题三维标注', '量测功能'],
    includeOrtho: false,
    include3D: true,
    estimatedTime: '30-60 分钟',
    credits: CREDIT_PRICES.TEMPLATE_3D
  },
  {
    id: 'full',
    name: '完整专业报告',
    description: '包含正射影像和三维模型的完整专业巡检报告',
    icon: '🎯',
    features: ['基础报告全部功能', '正射影像图', '三维实景模型', '专业报告排版', 'CAD导出'],
    includeOrtho: true,
    include3D: true,
    estimatedTime: '60-90 分钟',
    credits: CREDIT_PRICES.TEMPLATE_FULL,
    recommended: true
  }
]

onMounted(() => {
  if (!store.analysisResult) {
    router.push('/analysis')
    return
  }
  
  // 如果从后续步骤返回，自动选中之前的模板
  if (store.selectedTemplate) {
    selectedTemplateId.value = store.selectedTemplate.id
  }
})

const selectedTemplate = computed(() => {
  return templates.find(t => t.id === selectedTemplateId.value)
})

// 获取当前已选模板的积分
const currentTemplateCredits = computed(() => {
  if (!store.selectedTemplate) return 0
  return store.getTemplateCredits(store.selectedTemplate.id)
})

// 计算切换到目标模板需要的积分
const getRequiredCredits = (targetTemplateId) => {
  const targetCredits = store.getTemplateCredits(targetTemplateId)
  
  // 如果已支付过积分（已进入过进阶处理），计算差价
  if (store.paidTemplateCredits > 0) {
    return Math.max(0, targetCredits - store.paidTemplateCredits)
  }
  
  // 未支付过积分，显示完整价格
  return targetCredits
}

// 选择模板
const selectTemplate = (template) => {
  // 检查是否允许切换
  const switchResult = store.canSwitchTemplate(template.id)
  
  if (!switchResult.allowed) {
    // 不允许切换到低级模板
    switchWarning.value = switchResult.reason
    setTimeout(() => {
      switchWarning.value = ''
    }, 3000)
    return
  }
  
  selectedTemplateId.value = template.id
  switchWarning.value = ''
}

// 预览模板
const showPreview = (template) => {
  previewTemplate.value = template
}

const closePreview = () => {
  previewTemplate.value = null
}

// 判断是否需要显示额外资料上传弹窗
const needsSupplementaryUpload = computed(() => {
  const template = selectedTemplate.value
  return template?.includeOrtho || template?.include3D
})

// 下一步 - 保存模板选择并进入识别审查
const goNext = () => {
  if (!selectedTemplateId.value) return
  
  const template = selectedTemplate.value
  
  // 保存模板选择
  store.setSelectedTemplate(template)
  
  // 如果模板需要正射影像或3D模型，显示额外资料上传弹窗
  if (needsSupplementaryUpload.value && !store.hasSupplementaryData) {
    showSupplementaryModal.value = true
  } else {
    proceedToReview()
  }
}

// 继续进入识别审查页面
const proceedToReview = () => {
  store.setCurrentStep(4)
  router.push('/review')
}

// 处理额外资料上传确认
const handleSupplementaryConfirm = (uploadData) => {
  console.log('开始上传额外资料:', uploadData)
  
  // 添加文件到上传队列
  store.addSupplementaryFiles(uploadData.files, uploadData.dataSource)
  
  // 开始后台上传
  store.startSupplementaryUpload()
  
  // 关闭弹窗并继续
  showSupplementaryModal.value = false
  proceedToReview()
}

// 处理跳过额外资料上传
const handleSupplementarySkip = () => {
  showSupplementaryModal.value = false
  proceedToReview()
}

// 关闭额外资料上传弹窗
const closeSupplementaryModal = () => {
  showSupplementaryModal.value = false
}

// 返回
const goBack = () => {
  router.push('/analysis')
}
</script>

<template>
  <div class="max-w-6xl mx-auto animate-fade-in">
    <!-- 标题和积分显示 -->
    <div class="flex items-start justify-between mb-8">
      <div class="text-center flex-1">
        <h1 class="text-3xl font-bold text-white mb-2">选择报告模板</h1>
        <p class="text-white/60">
          当前场景：<span class="text-brand-sky">{{ store.analysisResult?.sceneName || '未识别' }}</span>
          · 根据您的需求选择合适的报告类型
        </p>
        <!-- 进阶处理完成提示 -->
        <p v-if="store.isAdvancedProcessed" class="text-accent-warning text-sm mt-2">
          ⚠️ 已生成进阶报告，只能升级到更高级的模板
        </p>
      </div>
      <CreditsDisplay />
    </div>
    
    <!-- 切换警告提示 -->
    <div v-if="switchWarning" class="glass-card p-4 mb-4 bg-accent-danger/20 border border-accent-danger/50">
      <div class="flex items-center gap-2 text-accent-danger">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <span>{{ switchWarning }}</span>
      </div>
    </div>
    
    <!-- 模板卡片 -->
    <div class="grid grid-cols-2 gap-6 mb-8">
      <div 
        v-for="template in templates"
        :key="template.id"
        @click="selectTemplate(template)"
        class="glass-card-hover p-6 cursor-pointer relative"
        :class="{
          'ring-2 ring-brand-primary': selectedTemplateId === template.id
        }"
      >
        <!-- 推荐标签 -->
        <div 
          v-if="template.recommended"
          class="absolute -top-3 -right-3 px-3 py-1 bg-accent-warning text-white text-xs font-bold rounded-full"
        >
          推荐
        </div>
        
        <!-- 选中指示器 -->
        <div 
          v-if="selectedTemplateId === template.id"
          class="absolute top-4 left-4 w-6 h-6 rounded-full bg-brand-primary flex items-center justify-center"
        >
          <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        
        <div class="flex items-start gap-4 mb-4">
          <div class="text-4xl">{{ template.icon }}</div>
          <div class="flex-1">
            <h3 class="text-xl font-semibold text-white mb-1">{{ template.name }}</h3>
            <p class="text-white/50 text-sm">{{ template.description }}</p>
          </div>
        </div>
        
        <!-- 功能列表 -->
        <div class="space-y-2 mb-4">
          <div 
            v-for="feature in template.features"
            :key="feature"
            class="flex items-center gap-2 text-sm text-white/70"
          >
            <svg class="w-4 h-4 text-accent-success flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            {{ feature }}
          </div>
        </div>
        
        <!-- 积分和时间 -->
        <div class="flex items-center justify-between pt-4 border-t border-white/10">
          <div class="flex items-center gap-2 text-sm text-white/50">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {{ template.estimatedTime }}
          </div>
          <div class="flex items-center gap-1">
            <svg class="w-4 h-4" :class="template.credits === 0 ? 'text-accent-success' : 'text-brand-sky'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span 
              class="text-lg font-bold font-mono"
              :class="template.credits === 0 ? 'text-accent-success' : 'text-brand-sky'"
            >
              {{ template.credits === 0 ? '免费' : template.credits }}
            </span>
            <span v-if="template.credits > 0" class="text-sm text-white/50">积分</span>
          </div>
        </div>
        
        <!-- 升级差价提示 -->
        <div v-if="store.isAdvancedProcessed && store.selectedTemplate?.id !== template.id" class="mt-2 text-xs text-center">
          <span v-if="getRequiredCredits(template.id) > 0" class="text-accent-warning">
            需补 {{ getRequiredCredits(template.id) }} 积分
          </span>
          <span v-else-if="getRequiredCredits(template.id) === 0" class="text-accent-success">
            无需补差价
          </span>
        </div>
        
        <!-- 预览按钮 -->
        <button 
          @click.stop="showPreview(template)"
          class="mt-4 w-full py-2 text-center text-sm text-white/60 hover:text-white border border-white/10 rounded-lg hover:bg-white/5 transition-colors"
        >
          查看模板预览
        </button>
      </div>
    </div>
    
    <!-- 选中模板信息 -->
    <div v-if="selectedTemplate" class="glass-card p-6 mb-6">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div class="text-3xl">{{ selectedTemplate.icon }}</div>
          <div>
            <div class="text-white font-semibold">已选择：{{ selectedTemplate.name }}</div>
            <div class="text-white/50 text-sm">
              预计处理时间 {{ selectedTemplate.estimatedTime }}
              <span v-if="selectedTemplate.includeOrtho"> · 含正射影像</span>
              <span v-if="selectedTemplate.include3D"> · 含三维模型</span>
            </div>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <svg class="w-6 h-6" :class="selectedTemplate.credits === 0 ? 'text-accent-success' : 'text-brand-sky'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
              d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div class="text-2xl font-bold font-mono" :class="selectedTemplate.credits === 0 ? 'text-accent-success' : 'text-brand-sky'">
            {{ selectedTemplate.credits === 0 ? '免费' : selectedTemplate.credits }}
          </div>
          <span v-if="selectedTemplate.credits > 0" class="text-white/50">积分</span>
        </div>
      </div>
    </div>
    
    <!-- 操作按钮 -->
    <div class="flex items-center justify-between">
      <button @click="goBack" class="btn-secondary">
        <svg class="w-5 h-5 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 17l-5-5m0 0l5-5m-5 5h12" />
        </svg>
        返回场景分析
      </button>
      
      <button 
        @click="goNext"
        :disabled="!selectedTemplateId"
        class="btn-primary"
      >
        开始识别检测
        <svg class="w-5 h-5 ml-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
        </svg>
      </button>
    </div>
    
    <!-- 报告预览弹窗 -->
    <ReportPreviewModal
      v-if="previewTemplate"
      :template="previewTemplate"
      :scene-type="store.analysisResult?.sceneType || 'road'"
      @close="closePreview"
    />
    
    <!-- 额外资料上传弹窗 -->
    <SupplementaryUploadModal
      :show="showSupplementaryModal"
      :template-type="selectedTemplateId"
      @confirm="handleSupplementaryConfirm"
      @skip="handleSupplementarySkip"
      @close="closeSupplementaryModal"
    />
  </div>
</template>

