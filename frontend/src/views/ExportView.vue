<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '../stores/project'
import CreditsDisplay from '../components/CreditsDisplay.vue'
import ReportPreviewModal from '../components/ReportPreviewModal.vue'
import api from '../api'

const router = useRouter()
const store = useProjectStore()

const isGenerating = ref(false)
const generateProgress = ref(0)
const reportGenerated = ref(false)
const exportFormat = ref('pdf')
const showPreviewModal = ref(false)
const isDownloading = ref(false)
const downloadError = ref('')

// 用户填写信息
const projectInfo = reactive({
  name: '',
  area: '',
  inspector: '',
  company: '',
  phone: '',
  email: '',
  logo: null,
  notes: '',
  reviewedBy: '',
  approvedBy: ''
})

// 天气信息（手动输入）
const weatherInfo = reactive({
  condition: '晴',  // 晴、多云、阴、小雨、中雨、大雨
  tempMin: '',
  tempMax: '',
  windLevel: ''
})

// 自动提取的元数据
const autoMetadata = computed(() => {
  const images = store.uploadedImages
  
  if (!images || images.length === 0) {
    return {
      inspectionPeriod: '—',
      gpsRange: '—',
      deviceInfo: '—',
      totalSize: '—',
      avgAltitude: '—',
      gsd: '—'
    }
  }
  
  // 提取拍摄时间范围（模拟）
  const startDate = new Date()
  const endDate = new Date()
  const inspectionPeriod = `${startDate.toLocaleDateString('zh-CN')} ${startDate.toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit'})} ~ ${endDate.toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit'})}`
  
  // 提取GPS范围
  const gpsCoords = images.map(img => ({
    lat: img.gps_lat || (31.2 + Math.random() * 0.1),
    lng: img.gps_lng || (121.4 + Math.random() * 0.1)
  }))
  
  const minLat = Math.min(...gpsCoords.map(c => c.lat))
  const maxLat = Math.max(...gpsCoords.map(c => c.lat))
  const minLng = Math.min(...gpsCoords.map(c => c.lng))
  const maxLng = Math.max(...gpsCoords.map(c => c.lng))
  const centerLat = (minLat + maxLat) / 2
  const centerLng = (minLng + maxLng) / 2
  
  const gpsRange = `中心: ${centerLat.toFixed(5)}, ${centerLng.toFixed(5)}`
  
  // 设备信息（模拟）
  const deviceInfo = 'DJI Mavic 3 + Hasselblad L2D-20c'
  
  // 计算总文件大小
  const totalSize = images.reduce((sum, img) => sum + (img.file_size || 0), 0)
  const totalSizeMB = (totalSize / 1024 / 1024).toFixed(2)
  
  // 平均飞行高度（模拟）
  const avgAltitude = '80m AGL'
  
  // GSD（模拟）
  const gsd = '约 2.2 cm/pixel'
  
  return {
    inspectionPeriod,
    gpsRange,
    gpsBounds: { minLat, maxLat, minLng, maxLng, centerLat, centerLng },
    deviceInfo,
    totalSize: `${totalSizeMB} MB`,
    avgAltitude,
    gsd
  }
})

// AI分析信息
const aiInfo = computed(() => {
  const reportIdPrefix = {
    'building': 'FCD',
    'solar': 'PV',
    'road': 'ROAD',
    'power': 'PWR'
  }[store.analysisResult?.sceneType] || 'RPT'
  
  const date = new Date()
  const dateStr = date.toISOString().split('T')[0].replace(/-/g, '')
  const randomId = Math.floor(Math.random() * 10000).toString().padStart(4, '0')
  
  return {
    reportId: `${reportIdPrefix}-${dateStr}-${randomId}`,
    traceId: `trace-${Math.random().toString(36).substring(2, 15)}`,
    pipelineId: `PIPE-${store.analysisResult?.sceneType?.toUpperCase() || 'UNKNOWN'}-2025.12`,
    modelVersions: store.analysisResult?.algorithms?.map((algo, index) => ({
      name: algo,
      version: `${Math.floor(Math.random() * 3) + 1}.${Math.floor(Math.random() * 5)}.${Math.floor(Math.random() * 10)}`
    })) || [],
    generatedAt: date.toISOString(),
    reportVersion: 'v1.0'
  }
})

onMounted(() => {
  // 设置当前步骤为步骤6（报告导出）
  store.setCurrentStep(6)

  if (!store.detectionResults.length) {
    router.push('/review')
  }
})

// 生成报告
const generateReport = async () => {
  isGenerating.value = true
  generateProgress.value = 0
  
  // 保存项目信息
  store.setProjectInfo({
    ...projectInfo,
    ...autoMetadata.value,
    ...aiInfo.value,
    weather: `${weatherInfo.condition} ${weatherInfo.tempMin}-${weatherInfo.tempMax}℃`
  })
  
  // 模拟生成过程
  const interval = setInterval(() => {
    generateProgress.value += Math.random() * 15
    if (generateProgress.value >= 100) {
      generateProgress.value = 100
      clearInterval(interval)
      reportGenerated.value = true
      isGenerating.value = false
      store.setProjectCompleted(true)
    }
  }, 200)
}

// 打开预览弹窗
const openPreview = () => {
  showPreviewModal.value = true
}

// 关闭预览弹窗
const closePreview = () => {
  showPreviewModal.value = false
}

// 构建完整的项目数据对象用于预览和导出
const fullProjectData = computed(() => {
  return {
    ...projectInfo,
    ...autoMetadata.value,
    ...aiInfo.value,
    weather: `${weatherInfo.condition} ${weatherInfo.tempMin}-${weatherInfo.tempMax}℃`
  }
})

// 下载报告
const downloadReport = async () => {
  if (isDownloading.value) return
  
  isDownloading.value = true
  downloadError.value = ''
  
  try {
    // 准备报告数据
    const reportData = {
      format: exportFormat.value,
      projectInfo: fullProjectData.value,
      detectionResults: store.detectionResults,
      statistics: store.statistics,
      analysisResult: store.analysisResult,
      template: store.selectedTemplate
    }
    
    // 调用后端生成PDF
    const response = await api.export.generatePDF(reportData)
    
    // 创建下载链接
    const blob = new Blob([response], { type: exportFormat.value === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    // 生成文件名
    const date = new Date().toISOString().split('T')[0]
    const projectName = projectInfo.name || '巡检报告'
    link.download = `${projectName}_${date}.${exportFormat.value}`
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
  } catch (error) {
    console.error('下载报告失败:', error)
    downloadError.value = '下载失败，请稍后重试'
  } finally {
    isDownloading.value = false
  }
}


// 新建项目
const newProject = () => {
  store.resetProject()
  router.push('/')
}
</script>

<template>
  <div class="max-w-7xl mx-auto animate-fade-in">
    <!-- 标题和积分 -->
    <div class="flex items-start justify-between mb-8">
      <div class="text-center flex-1">
        <h1 class="text-2xl font-bold text-text-primary mb-2">报告导出</h1>
        <p class="text-brand-muted text-sm">填写项目信息，生成并导出巡检报告</p>
      </div>
      <CreditsDisplay />
    </div>
    
    <!-- 报告已生成状态 -->
    <div v-if="reportGenerated" class="text-center">
      <div class="glass-card p-12 mb-6">
        <div class="success-icon">
          <svg class="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        
        <h2 class="text-xl font-bold text-text-primary mb-2">报告生成完成！</h2>
        <p class="text-brand-muted text-sm mb-8">您的巡检报告已准备就绪，请选择格式下载</p>
        
        <!-- 报告摘要 -->
        <div class="grid grid-cols-4 gap-4 mb-8">
          <div class="summary-stat">
            <div class="text-2xl font-bold text-text-primary">{{ store.statistics.totalImages }}</div>
            <div class="text-xs text-brand-muted">总图片数</div>
          </div>
          <div class="summary-stat">
            <div class="text-2xl font-bold text-accent-danger">
              {{ store.detectionResults.filter(r => r.status === 'danger').length }}
            </div>
            <div class="text-xs text-brand-muted">严重问题</div>
          </div>
          <div class="summary-stat">
            <div class="text-2xl font-bold text-accent-warning">
              {{ store.detectionResults.filter(r => r.status === 'warning').length }}
            </div>
            <div class="text-xs text-brand-muted">一般问题</div>
          </div>
          <div class="summary-stat">
            <div class="text-2xl font-bold text-brand-primary">
              {{ store.statistics.issueCount }}
            </div>
            <div class="text-xs text-brand-muted">问题总数</div>
          </div>
        </div>
        
        <!-- 下载格式选择 -->
        <div class="flex items-center justify-center gap-4 mb-6">
          <label 
            class="format-option"
            :class="{ 'active': exportFormat === 'pdf' }"
          >
            <input type="radio" v-model="exportFormat" value="pdf" class="hidden">
            <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 2l5 5h-5V4zM8.5 13H10v4.5H8.5V13zm3 0h3c.55 0 1 .45 1 1v2.5c0 .55-.45 1-1 1H13v1h2v1.5h-3.5V13zm1.5 3h1v-1.5h-1V16zM6 13h2.5c.83 0 1.5.67 1.5 1.5v1c0 .83-.67 1.5-1.5 1.5H7.5v1.5H6V13zm1.5 2.5H8c.28 0 .5-.22.5-.5v-1c0-.28-.22-.5-.5-.5h-.5v2z"/>
            </svg>
            <div class="text-left">
              <div class="font-semibold text-sm">PDF 格式</div>
              <div class="text-xs opacity-70">适合打印和分享</div>
            </div>
          </label>
          
          <label 
            class="format-option"
            :class="{ 'active': exportFormat === 'word' }"
          >
            <input type="radio" v-model="exportFormat" value="word" class="hidden">
            <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 2l5 5h-5V4zM7 17l1.5-6h1.2l.9 3.6.9-3.6h1.2l1.5 6h-1.3l-.8-3.5-.9 3.5H10l-.9-3.5-.8 3.5H7z"/>
            </svg>
            <div class="text-left">
              <div class="font-semibold text-sm">Word 格式</div>
              <div class="text-xs opacity-70">可编辑修改</div>
            </div>
          </label>
        </div>
        
        <!-- 下载按钮 -->
        <div class="flex flex-col items-center gap-4">
          <div class="flex items-center justify-center gap-4">
            <button 
              @click="downloadReport" 
              :disabled="isDownloading"
              class="btn-primary"
              :class="{ 'opacity-50 cursor-not-allowed': isDownloading }"
            >
              <svg v-if="isDownloading" class="w-5 h-5 mr-2 inline animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <svg v-else class="w-5 h-5 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              {{ isDownloading ? '生成中...' : '下载报告' }}
            </button>
            
            <button @click="openPreview" class="btn-secondary">
              <svg class="w-5 h-5 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              预览报告
            </button>
            
            <button @click="newProject" class="btn-secondary">
              <svg class="w-5 h-5 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
              新建项目
            </button>
          </div>
          
          <!-- 错误提示 -->
          <div v-if="downloadError" class="text-accent-danger text-sm">
            {{ downloadError }}
          </div>
        </div>
      </div>
    </div>
    
    <!-- 填写信息表单 -->
    <div v-else>
      <!-- 生成中状态 -->
      <div v-if="isGenerating" class="glass-card p-12 text-center mb-6">
        <div class="generating-spinner">
          <div class="generating-ring"></div>
          <div class="generating-icon">
            <svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
        </div>
        
        <h3 class="text-lg font-semibold text-text-primary mb-2">正在生成报告...</h3>
        <p class="text-brand-muted text-sm mb-6">正在整合检测结果和项目信息</p>
        
        <div class="max-w-md mx-auto">
          <div class="flex items-center justify-between mb-2 text-sm">
            <span class="text-brand-muted">生成进度</span>
            <span class="text-brand-primary font-mono font-bold">{{ Math.round(generateProgress) }}%</span>
          </div>
          <div class="progress-bar-gen">
            <div 
              class="progress-fill-gen"
              :style="{ width: `${generateProgress}%` }"
            ></div>
          </div>
        </div>
      </div>
      
      <!-- 表单 - 左右布局 -->
      <div v-else class="grid grid-cols-3 gap-6">
        <!-- 左侧：表单区域 -->
        <div class="col-span-2 space-y-6">
          <!-- 基本信息 -->
          <div class="glass-card p-6">
            <h3 class="section-title text-text-primary mb-4">
              <span class="flex items-center gap-2">
                <svg class="w-5 h-5 text-brand-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                基本信息
              </span>
              <span class="text-xs text-text-secondary font-normal">必填</span>
            </h3>
            
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="form-label">项目名称 *</label>
                <input 
                  v-model="projectInfo.name"
                  type="text" 
                  class="input-field"
                  placeholder="请输入项目名称"
                >
              </div>
              <div>
                <label class="form-label">巡检范围/区域 *</label>
                <input 
                  v-model="projectInfo.area"
                  type="text" 
                  class="input-field"
                  placeholder="例如：XX路 K12+000 ~ K18+500"
                >
              </div>
              <div>
                <label class="form-label">巡检人员</label>
                <input 
                  v-model="projectInfo.inspector"
                  type="text" 
                  class="input-field"
                  placeholder="请输入巡检人员姓名"
                >
              </div>
              <div>
                <label class="form-label">所属公司/单位</label>
                <input 
                  v-model="projectInfo.company"
                  type="text" 
                  class="input-field"
                  placeholder="请输入公司名称"
                >
              </div>
              <div>
                <label class="form-label">联系电话</label>
                <input 
                  v-model="projectInfo.phone"
                  type="tel" 
                  class="input-field"
                  placeholder="请输入联系电话"
                >
              </div>
              <div>
                <label class="form-label">联系邮箱</label>
                <input 
                  v-model="projectInfo.email"
                  type="email" 
                  class="input-field"
                  placeholder="请输入联系邮箱"
                >
              </div>
            </div>
          </div>
          
          <!-- 任务信息（自动识别+手动补充） -->
          <div class="glass-card p-6">
            <h3 class="section-title text-text-primary mb-4">
              <span class="flex items-center gap-2">
                <svg class="w-5 h-5 text-brand-cyan" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                任务信息
              </span>
              <span class="text-xs text-brand-cyan font-normal">🤖 自动识别 + 手动补充</span>
            </h3>
            
            <!-- 自动识别字段（只读显示） -->
            <div class="grid grid-cols-2 gap-4 mb-4">
              <div class="auto-field">
                <label class="form-label flex items-center gap-1">
                  <span>📍 巡检时间</span>
                  <span class="text-xs text-brand-cyan">自动</span>
                </label>
                <div class="auto-value">{{ autoMetadata.inspectionPeriod }}</div>
              </div>
              <div class="auto-field">
                <label class="form-label flex items-center gap-1">
                  <span>🌍 GPS范围</span>
                  <span class="text-xs text-brand-cyan">自动</span>
                </label>
                <div class="auto-value">{{ autoMetadata.gpsRange }}</div>
              </div>
              <div class="auto-field">
                <label class="form-label flex items-center gap-1">
                  <span>🛸 采集设备</span>
                  <span class="text-xs text-brand-cyan">自动</span>
                </label>
                <div class="auto-value">{{ autoMetadata.deviceInfo }}</div>
              </div>
              <div class="auto-field">
                <label class="form-label flex items-center gap-1">
                  <span>📐 GSD</span>
                  <span class="text-xs text-brand-cyan">自动</span>
                </label>
                <div class="auto-value">{{ autoMetadata.gsd }}</div>
              </div>
              <div class="auto-field">
                <label class="form-label flex items-center gap-1">
                  <span>📏 飞行高度</span>
                  <span class="text-xs text-brand-cyan">自动</span>
                </label>
                <div class="auto-value">{{ autoMetadata.avgAltitude }}</div>
              </div>
              <div class="auto-field">
                <label class="form-label flex items-center gap-1">
                  <span>💾 总文件大小</span>
                  <span class="text-xs text-brand-cyan">自动</span>
                </label>
                <div class="auto-value">{{ autoMetadata.totalSize }}</div>
              </div>
            </div>
            
            <!-- 天气信息（手动输入） -->
            <div class="border-t border-white/10 pt-4">
              <label class="form-label mb-3">🌤️ 天气信息（可选）</label>
              <div class="grid grid-cols-4 gap-4">
                <div>
                  <select v-model="weatherInfo.condition" class="input-field">
                    <option value="晴">晴</option>
                    <option value="多云">多云</option>
                    <option value="阴">阴</option>
                    <option value="小雨">小雨</option>
                    <option value="中雨">中雨</option>
                    <option value="大雨">大雨</option>
                  </select>
                </div>
                <div>
                  <input 
                    v-model="weatherInfo.tempMin"
                    type="number" 
                    class="input-field"
                    placeholder="最低温(℃)"
                  >
                </div>
                <div>
                  <input 
                    v-model="weatherInfo.tempMax"
                    type="number" 
                    class="input-field"
                    placeholder="最高温(℃)"
                  >
                </div>
                <div>
                  <input 
                    v-model="weatherInfo.windLevel"
                    type="text" 
                    class="input-field"
                    placeholder="风力等级"
                  >
                </div>
              </div>
            </div>
          </div>
          
          <!-- AI分析信息（自动生成） -->
          <div class="glass-card p-6">
            <h3 class="section-title text-text-primary mb-4">
              <span class="flex items-center gap-2">
                <svg class="w-5 h-5 text-accent-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                AI分析信息
              </span>
              <span class="text-xs text-accent-success font-normal">🤖 自动生成</span>
            </h3>
            
            <div class="space-y-3">
              <div class="auto-field">
                <label class="form-label">报告编号</label>
                <div class="auto-value font-mono">{{ aiInfo.reportId }}</div>
              </div>
              <div class="auto-field">
                <label class="form-label">Pipeline ID</label>
                <div class="auto-value font-mono">{{ aiInfo.pipelineId }}</div>
              </div>
              <div class="auto-field">
                <label class="form-label">Trace ID</label>
                <div class="auto-value font-mono text-xs">{{ aiInfo.traceId }}</div>
              </div>
              <div class="auto-field">
                <label class="form-label">场景类型</label>
                <div class="auto-value">{{ store.analysisResult?.sceneName || '—' }}</div>
              </div>
              <div class="auto-field">
                <label class="form-label">使用的算法</label>
                <div class="flex flex-wrap gap-2 mt-2">
                  <span 
                    v-for="algo in store.analysisResult?.algorithms"
                    :key="algo"
                    class="px-3 py-1 bg-brand-primary/20 text-brand-sky text-xs rounded-full"
                  >
                    {{ algo }}
                  </span>
                </div>
              </div>
              <div class="auto-field">
                <label class="form-label">模型版本</label>
                <div class="flex flex-wrap gap-2 mt-2">
                  <span 
                    v-for="model in aiInfo.modelVersions"
                    :key="model.name"
                    class="px-3 py-1 bg-accent-success/20 text-accent-success text-xs rounded font-mono"
                  >
                    {{ model.name }} v{{ model.version }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 合规/审计信息 -->
          <div class="glass-card p-6">
            <h3 class="section-title text-text-primary mb-4">
              <span class="flex items-center gap-2">
                <svg class="w-5 h-5 text-accent-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                合规/审计信息
              </span>
              <span class="text-xs text-text-secondary font-normal">可选</span>
            </h3>
            
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="form-label">复核人员</label>
                <input 
                  v-model="projectInfo.reviewedBy"
                  type="text" 
                  class="input-field"
                  placeholder="请输入复核人员"
                >
              </div>
              <div>
                <label class="form-label">审批人员</label>
                <input 
                  v-model="projectInfo.approvedBy"
                  type="text" 
                  class="input-field"
                  placeholder="请输入审批人员"
                >
              </div>
              <div class="col-span-2">
                <label class="form-label">备注信息</label>
                <textarea 
                  v-model="projectInfo.notes"
                  class="input-field min-h-[80px] resize-none"
                  placeholder="添加额外的备注信息（可选）"
                ></textarea>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 右侧：预览区域 -->
        <div class="space-y-6">
          <!-- 报告预览 -->
          <div class="glass-card p-6 sticky top-6">
            <h3 class="section-title text-text-primary mb-4">报告预览</h3>
            
            <!-- 统计数据 -->
            <div class="space-y-3 mb-6">
              <div class="preview-stat">
                <span class="text-text-secondary text-sm">总图片数</span>
                <span class="text-text-primary font-bold font-mono">{{ store.statistics.totalImages }}</span>
              </div>
              <div class="preview-stat">
                <span class="text-text-secondary text-sm">问题总数</span>
                <span class="text-accent-danger font-bold font-mono">{{ store.statistics.issueCount }}</span>
              </div>
              <div class="preview-stat">
                <span class="text-text-secondary text-sm">平均置信度</span>
                <span class="text-brand-sky font-bold font-mono">{{ store.statistics.avgConfidence }}%</span>
              </div>
              <div class="preview-stat">
                <span class="text-text-secondary text-sm">场景类型</span>
                <span class="text-text-primary font-bold">{{ store.analysisResult?.sceneName }}</span>
              </div>
              <div class="preview-stat">
                <span class="text-text-secondary text-sm">报告模板</span>
                <span class="text-text-primary font-bold">{{ store.selectedTemplate?.name }}</span>
              </div>
            </div>
            
            <!-- 预览完整报告按钮 -->
            <button 
              @click="openPreview"
              class="w-full py-3 mb-4 text-center text-sm font-medium text-brand-sky border border-brand-sky/30 rounded-xl hover:bg-brand-sky/10 transition-all flex items-center justify-center gap-2"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              预览完整报告
            </button>
            
            <!-- 报告包含 -->
            <div class="border-t border-line-light pt-4">
              <div class="text-sm text-text-secondary mb-3">报告包含：</div>
              <div class="space-y-2 text-sm">
                <div class="flex items-center gap-2 text-text-primary">
                  <svg class="w-4 h-4 text-accent-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span>封面信息 / 报告摘要</span>
                </div>
                <div class="flex items-center gap-2 text-text-primary">
                  <svg class="w-4 h-4 text-accent-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span>任务信息 / 设备参数</span>
                </div>
                <div class="flex items-center gap-2 text-text-primary">
                  <svg class="w-4 h-4 text-accent-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span>AI分析说明</span>
                </div>
                <div class="flex items-center gap-2 text-text-primary">
                  <svg class="w-4 h-4 text-accent-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span>问题清单</span>
                </div>
                <div class="flex items-center gap-2 text-text-primary">
                  <svg class="w-4 h-4 text-accent-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span>问题详情（含证据图）</span>
                </div>
                <div v-if="store.selectedTemplate?.includeOrtho" class="flex items-center gap-2 text-text-primary">
                  <svg class="w-4 h-4 text-accent-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span>正射影像图</span>
                </div>
                <div v-if="store.selectedTemplate?.include3D" class="flex items-center gap-2 text-text-primary">
                  <svg class="w-4 h-4 text-accent-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span>三维模型</span>
                </div>
                <div class="flex items-center gap-2 text-text-primary">
                  <svg class="w-4 h-4 text-accent-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span>审计/追溯信息</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 操作按钮 -->
      <div class="flex justify-end mt-6">
        <button
          @click="generateReport"
          :disabled="!projectInfo.name || !projectInfo.area"
          class="btn-primary"
        >
          生成报告
          <svg class="w-5 h-5 ml-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </button>
      </div>
    </div>
    
    <!-- 报告预览弹窗 -->
    <ReportPreviewModal
      v-if="showPreviewModal"
      :template="store.selectedTemplate || { id: 'basic', name: '基础检测报告' }"
      :scene-type="store.analysisResult?.sceneType || 'road'"
      :use-real-data="true"
      :project-data="fullProjectData"
      @close="closePreview"
    />
  </div>
</template>

<style scoped>
.success-icon {
  width: 96px;
  height: 96px;
  margin: 0 auto 24px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(111,188,206,0.2), rgba(111,188,206,0.1));
  border: 1px solid rgba(111,188,206,0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--good);
}

.summary-stat {
  text-align: center;
  padding: 16px;
  border-radius: 12px;
  background: rgba(245,245,245,0.6);
  border: 1px solid var(--line-light);
}

.format-option {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.18s ease;
  border: 1px solid var(--line);
  background: rgba(255,255,255,0.8);
  color: var(--muted);
}

.format-option:hover {
  background: rgba(245,245,245,0.9);
  border-color: rgba(16,35,117,0.25);
  color: var(--text);
}

.format-option.active {
  background: rgba(16,35,117,0.1);
  border-color: rgba(16,35,117,0.4);
  color: var(--text);
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-label {
  display: block;
  font-size: 12px;
  color: var(--muted);
  margin-bottom: 8px;
}

.auto-field {
  padding: 12px;
  border-radius: 10px;
  background: rgba(16, 35, 117, 0.05);
  border: 1px solid rgba(16, 35, 117, 0.15);
}

.auto-value {
  color: var(--text);
  font-size: 14px;
  margin-top: 4px;
  word-break: break-all;
}

.preview-stat {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(245,245,245,0.6);
  border: 1px solid var(--line-light);
}

.generating-spinner {
  width: 96px;
  height: 96px;
  margin: 0 auto 24px;
  position: relative;
}

.generating-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 4px solid rgba(16,35,117,0.2);
}

.generating-ring::after {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  border: 4px solid transparent;
  border-top-color: var(--brand);
  animation: spin 1s linear infinite;
}

.generating-icon {
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

.progress-bar-gen {
  height: 8px;
  background: rgba(245,245,245,0.8);
  border-radius: 999px;
  overflow: hidden;
  border: 1px solid var(--line-light);
}

.progress-fill-gen {
  height: 100%;
  background: linear-gradient(90deg, var(--brand), var(--good));
  border-radius: 999px;
  transition: width 0.3s ease;
}
</style>
