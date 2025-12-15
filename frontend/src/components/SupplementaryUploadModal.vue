<script setup>
import { ref, computed, watch } from 'vue'
import { useProjectStore } from '../stores/project'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  templateType: {
    type: String,
    default: 'full' // ortho, 3d, full
  }
})

const emit = defineEmits(['confirm', 'skip', 'close'])

const store = useProjectStore()

// 数据来源软件列表
const dataSources = [
  {
    id: 'dji_terra',
    name: '大疆智图',
    icon: '🛸',
    description: 'DJI Terra',
    formats: {
      pos: ['.csv', '.txt'],
      sfm: [],
      ortho: ['.tif', '.tiff'],
      model3d: ['.obj', '.b3dm']
    }
  },
  {
    id: 'metashape',
    name: 'Metashape',
    icon: '📐',
    description: 'Agisoft Metashape',
    formats: {
      pos: ['.csv', '.xml'],
      sfm: ['.psx', '.psz'],
      ortho: ['.tif', '.tiff'],
      model3d: ['.obj', '.ply']
    }
  },
  {
    id: 'pix4d',
    name: 'Pix4D',
    icon: '🗺️',
    description: 'Pix4Dmapper',
    formats: {
      pos: ['.csv'],
      sfm: ['.p4d'],
      ortho: ['.tif', '.tiff'],
      model3d: ['.obj', '.ply']
    }
  },
  {
    id: 'context_capture',
    name: 'Context Capture',
    icon: '🏗️',
    description: 'Bentley ContextCapture',
    formats: {
      pos: ['.csv'],
      sfm: ['.xml'],
      ortho: ['.tif', '.tiff'],
      model3d: ['.obj', '.3mx', '.osgb']
    }
  },
  {
    id: 'other',
    name: '其他/自定义',
    icon: '📁',
    description: '通用格式',
    formats: {
      pos: ['.csv', '.txt', '.xml'],
      sfm: [],
      ortho: ['.tif', '.tiff', '.jpg', '.png'],
      model3d: ['.obj', '.ply', '.fbx', '.glb', '.gltf']
    }
  }
]

// 可上传的文件类型
const fileTypes = computed(() => {
  const types = [
    {
      id: 'pos',
      name: 'PoS/轨迹信息',
      description: '位置与姿态信息，包含飞行轨迹坐标',
      icon: '📍',
      discount: 10,
      timeSaved: '10-15分钟',
      always: true
    },
    {
      id: 'sfm',
      name: 'SfM结果',
      description: '已计算好的空三加密结果',
      icon: '📊',
      discount: 30,
      timeSaved: '30-60分钟',
      always: true
    }
  ]
  
  if (props.templateType === 'ortho' || props.templateType === 'full') {
    types.push({
      id: 'ortho',
      name: '正射影像图',
      description: '已生成的正射影像图',
      icon: '🗺️',
      discount: 50,
      timeSaved: '跳过正射生成',
      always: false
    })
  }
  
  if (props.templateType === '3d' || props.templateType === 'full') {
    types.push({
      id: 'model3d',
      name: '三维模型',
      description: '已重建的三维实景模型',
      icon: '🏛️',
      discount: 50,
      timeSaved: '跳过模型重建',
      always: false
    })
  }
  
  return types
})

// 当前选择的数据来源
const selectedSource = ref('dji_terra')

// 当前选择要上传的文件类型
const selectedFileTypes = ref([])

// 已选择的文件
const selectedFiles = ref({
  pos: null,
  sfm: null,
  ortho: null,
  model3d: null
})

// 当前步骤 1: 选择来源, 2: 选择文件类型, 3: 上传文件
const currentStep = ref(1)

// 重置状态
const resetState = () => {
  selectedSource.value = 'dji_terra'
  selectedFileTypes.value = []
  selectedFiles.value = {
    pos: null,
    sfm: null,
    ortho: null,
    model3d: null
  }
  currentStep.value = 1
}

// 监听show变化，重置状态
watch(() => props.show, (newVal) => {
  if (newVal) {
    resetState()
  }
})

// 获取当前数据来源的格式
const currentSourceFormats = computed(() => {
  const source = dataSources.find(s => s.id === selectedSource.value)
  return source?.formats || {}
})

// 获取文件类型的允许格式
const getAcceptFormats = (typeId) => {
  const formats = currentSourceFormats.value[typeId] || []
  return formats.join(',')
}

// 计算预计节省
const estimatedSavings = computed(() => {
  let discountPercent = 0
  let timeSavedList = []
  
  selectedFileTypes.value.forEach(typeId => {
    const type = fileTypes.value.find(t => t.id === typeId)
    if (type) {
      discountPercent += type.discount
      timeSavedList.push(type.timeSaved)
    }
  })
  
  // 限制最大折扣
  discountPercent = Math.min(discountPercent, 70)
  
  return {
    discountPercent,
    timeSavedList
  }
})

// 切换文件类型选择
const toggleFileType = (typeId) => {
  const index = selectedFileTypes.value.indexOf(typeId)
  if (index === -1) {
    selectedFileTypes.value.push(typeId)
  } else {
    selectedFileTypes.value.splice(index, 1)
    // 清除对应的文件
    selectedFiles.value[typeId] = null
  }
}

// 处理文件选择
const handleFileSelect = (typeId, event) => {
  const file = event.target.files[0]
  if (file) {
    selectedFiles.value[typeId] = {
      file,
      name: file.name,
      size: file.size,
      type: typeId
    }
  }
}

// 移除文件
const removeFile = (typeId) => {
  selectedFiles.value[typeId] = null
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`
}

// 检查是否可以进入下一步
const canProceedToStep2 = computed(() => selectedSource.value !== null)
const canProceedToStep3 = computed(() => selectedFileTypes.value.length > 0)
const canSubmit = computed(() => {
  // 检查所有选中的文件类型是否都有对应的文件
  return selectedFileTypes.value.every(typeId => selectedFiles.value[typeId] !== null)
})

// 下一步
const nextStep = () => {
  if (currentStep.value < 3) {
    currentStep.value++
  }
}

// 上一步
const prevStep = () => {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

// 跳过上传
const handleSkip = () => {
  emit('skip')
  emit('close')
}

// 确认上传
const handleConfirm = () => {
  const uploadData = {
    dataSource: selectedSource.value,
    files: Object.entries(selectedFiles.value)
      .filter(([key, value]) => value !== null)
      .map(([key, value]) => ({
        type: key,
        ...value
      })),
    estimatedSavings: estimatedSavings.value
  }
  
  emit('confirm', uploadData)
}

// 关闭弹窗
const handleClose = () => {
  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <div 
      v-if="show"
      class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      @click="handleClose"
    >
      <div 
        class="glass-card p-6 max-w-3xl w-full max-h-[90vh] overflow-auto animate-fade-in"
        @click.stop
      >
        <!-- 头部 -->
        <div class="flex items-center justify-between mb-6">
          <div>
            <h3 class="text-xl font-bold text-white">上传已有处理结果</h3>
            <p class="text-white/50 text-sm mt-1">上传已有资料可以加速处理并节省费用</p>
          </div>
          <button @click="handleClose" class="text-white/50 hover:text-white transition-colors">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <!-- 步骤指示器 -->
        <div class="flex items-center justify-center gap-2 mb-8">
          <div 
            v-for="step in 3" 
            :key="step"
            class="flex items-center"
          >
            <div 
              class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all"
              :class="{
                'bg-brand-primary text-white': currentStep >= step,
                'bg-white/10 text-white/30': currentStep < step
              }"
            >
              {{ step }}
            </div>
            <div 
              v-if="step < 3"
              class="w-12 h-0.5 mx-2 transition-all"
              :class="{
                'bg-brand-primary': currentStep > step,
                'bg-white/10': currentStep <= step
              }"
            ></div>
          </div>
        </div>
        
        <!-- 步骤1: 选择数据来源 -->
        <div v-if="currentStep === 1" class="animate-fade-in">
          <h4 class="text-lg font-semibold text-white mb-4">选择数据来源软件</h4>
          <p class="text-white/50 text-sm mb-6">选择生成这些数据的软件，以便我们更好地解析格式</p>
          
          <div class="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
            <button
              v-for="source in dataSources"
              :key="source.id"
              @click="selectedSource = source.id"
              class="p-4 rounded-xl border transition-all text-left"
              :class="{
                'border-brand-primary bg-brand-primary/10': selectedSource === source.id,
                'border-white/10 bg-white/5 hover:border-white/30': selectedSource !== source.id
              }"
            >
              <div class="text-2xl mb-2">{{ source.icon }}</div>
              <div class="font-medium text-white">{{ source.name }}</div>
              <div class="text-xs text-white/50">{{ source.description }}</div>
            </button>
          </div>
        </div>
        
        <!-- 步骤2: 选择文件类型 -->
        <div v-if="currentStep === 2" class="animate-fade-in">
          <h4 class="text-lg font-semibold text-white mb-4">选择要上传的数据类型</h4>
          <p class="text-white/50 text-sm mb-6">选择您已有的处理结果，可多选</p>
          
          <div class="space-y-3 mb-6">
            <button
              v-for="type in fileTypes"
              :key="type.id"
              @click="toggleFileType(type.id)"
              class="w-full p-4 rounded-xl border transition-all text-left flex items-start gap-4"
              :class="{
                'border-brand-primary bg-brand-primary/10': selectedFileTypes.includes(type.id),
                'border-white/10 bg-white/5 hover:border-white/30': !selectedFileTypes.includes(type.id)
              }"
            >
              <div class="text-2xl">{{ type.icon }}</div>
              <div class="flex-1">
                <div class="flex items-center justify-between">
                  <span class="font-medium text-white">{{ type.name }}</span>
                  <div class="flex items-center gap-2">
                    <span class="text-xs text-accent-success">节省 {{ type.discount }}%</span>
                    <div 
                      class="w-5 h-5 rounded border flex items-center justify-center"
                      :class="{
                        'bg-brand-primary border-brand-primary': selectedFileTypes.includes(type.id),
                        'border-white/30': !selectedFileTypes.includes(type.id)
                      }"
                    >
                      <svg v-if="selectedFileTypes.includes(type.id)" class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                  </div>
                </div>
                <div class="text-sm text-white/50 mt-1">{{ type.description }}</div>
                <div class="text-xs text-brand-sky mt-1">预计节省: {{ type.timeSaved }}</div>
              </div>
            </button>
          </div>
          
          <!-- 预计节省统计 -->
          <div v-if="selectedFileTypes.length > 0" class="glass-card p-4 bg-accent-success/10 border border-accent-success/30">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <svg class="w-5 h-5 text-accent-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span class="text-white text-sm">预计可节省积分</span>
              </div>
              <span class="text-accent-success font-bold text-lg">{{ estimatedSavings.discountPercent }}%</span>
            </div>
          </div>
        </div>
        
        <!-- 步骤3: 上传文件 -->
        <div v-if="currentStep === 3" class="animate-fade-in">
          <h4 class="text-lg font-semibold text-white mb-4">上传文件</h4>
          <p class="text-white/50 text-sm mb-6">为每种选中的数据类型选择对应文件</p>
          
          <div class="space-y-4 mb-6">
            <div 
              v-for="typeId in selectedFileTypes"
              :key="typeId"
              class="glass-card p-4"
            >
              <div class="flex items-center justify-between mb-3">
                <div class="flex items-center gap-2">
                  <span class="text-xl">{{ fileTypes.find(t => t.id === typeId)?.icon }}</span>
                  <span class="font-medium text-white">{{ fileTypes.find(t => t.id === typeId)?.name }}</span>
                </div>
                <span class="text-xs text-white/50">
                  支持格式: {{ getAcceptFormats(typeId) || '通用格式' }}
                </span>
              </div>
              
              <!-- 未选择文件 -->
              <div v-if="!selectedFiles[typeId]">
                <label 
                  class="flex items-center justify-center gap-2 p-6 border-2 border-dashed border-white/20 rounded-xl cursor-pointer hover:border-brand-primary/50 hover:bg-brand-primary/5 transition-all"
                >
                  <svg class="w-6 h-6 text-white/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <span class="text-white/50">点击选择文件或拖拽到此处</span>
                  <input 
                    type="file"
                    class="hidden"
                    :accept="getAcceptFormats(typeId)"
                    @change="handleFileSelect(typeId, $event)"
                  >
                </label>
              </div>
              
              <!-- 已选择文件 -->
              <div v-else class="flex items-center justify-between p-4 bg-white/5 rounded-xl">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-lg bg-brand-primary/20 flex items-center justify-center">
                    <svg class="w-5 h-5 text-brand-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div>
                    <div class="text-white text-sm font-medium truncate max-w-xs">{{ selectedFiles[typeId].name }}</div>
                    <div class="text-white/50 text-xs">{{ formatFileSize(selectedFiles[typeId].size) }}</div>
                  </div>
                </div>
                <button 
                  @click="removeFile(typeId)"
                  class="p-2 hover:bg-white/10 rounded-lg transition-colors"
                >
                  <svg class="w-5 h-5 text-white/50 hover:text-accent-danger" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
          
          <!-- 预计节省统计 -->
          <div class="glass-card p-4 bg-accent-success/10 border border-accent-success/30">
            <div class="flex items-center justify-between mb-2">
              <span class="text-white text-sm">预计节省积分</span>
              <span class="text-accent-success font-bold">{{ estimatedSavings.discountPercent }}%</span>
            </div>
            <div class="text-xs text-white/50">
              预计节省时间: {{ estimatedSavings.timeSavedList.join(', ') || '无' }}
            </div>
            <div class="text-xs text-white/40 mt-2">
              * 大文件将在后台上传，您可以继续进行其他操作
            </div>
          </div>
        </div>
        
        <!-- 底部按钮 -->
        <div class="flex items-center justify-between mt-8 pt-6 border-t border-white/10">
          <button 
            @click="handleSkip"
            class="text-white/50 hover:text-white transition-colors text-sm"
          >
            跳过，不上传额外资料
          </button>
          
          <div class="flex items-center gap-3">
            <button 
              v-if="currentStep > 1"
              @click="prevStep"
              class="px-5 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white font-medium transition-colors"
            >
              上一步
            </button>
            
            <button 
              v-if="currentStep < 3"
              @click="nextStep"
              :disabled="(currentStep === 1 && !canProceedToStep2) || (currentStep === 2 && !canProceedToStep3)"
              class="px-5 py-2.5 rounded-xl font-medium transition-colors"
              :class="{
                'bg-brand-primary hover:bg-brand-primary/80 text-white': (currentStep === 1 && canProceedToStep2) || (currentStep === 2 && canProceedToStep3),
                'bg-white/5 text-white/30 cursor-not-allowed': (currentStep === 1 && !canProceedToStep2) || (currentStep === 2 && !canProceedToStep3)
              }"
            >
              下一步
            </button>
            
            <button 
              v-if="currentStep === 3"
              @click="handleConfirm"
              :disabled="!canSubmit"
              class="px-5 py-2.5 rounded-xl font-medium transition-colors"
              :class="{
                'bg-brand-primary hover:bg-brand-primary/80 text-white': canSubmit,
                'bg-white/5 text-white/30 cursor-not-allowed': !canSubmit
              }"
            >
              开始上传
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
@keyframes fade-in {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.animate-fade-in {
  animation: fade-in 0.2s ease-out;
}

/* 自定义滚动条 */
.max-h-\[90vh\]::-webkit-scrollbar {
  width: 6px;
}

.max-h-\[90vh\]::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 3px;
}

.max-h-\[90vh\]::-webkit-scrollbar-thumb {
  background: rgba(91, 214, 255, 0.3);
  border-radius: 3px;
}

.max-h-\[90vh\]::-webkit-scrollbar-thumb:hover {
  background: rgba(91, 214, 255, 0.5);
}
</style>

