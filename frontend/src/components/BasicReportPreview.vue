<script setup>
import { computed } from 'vue'
import { useProjectStore } from '../stores/project'

const store = useProjectStore()
const emit = defineEmits(['downloadBasic'])

// 按严重程度分组问题
const issuesByType = computed(() => {
  const groups = {
    danger: [],
    warning: [],
    caution: []
  }
  
  store.detectionResults.forEach(result => {
    result.issues.forEach(issue => {
      if (groups[issue.severity]) {
        groups[issue.severity].push({
          ...issue,
          imageName: result.name,
          imageId: result.id
        })
      }
    })
  })
  
  return groups
})

// 问题总数
const totalIssues = computed(() => {
  return issuesByType.value.danger.length + 
         issuesByType.value.warning.length + 
         issuesByType.value.caution.length
})

// 导出基础报告 - 跳转到导出页面
const downloadBasicReport = async () => {
  emit('downloadBasic')
}

const getSeverityColor = (severity) => {
  switch (severity) {
    case 'danger': return 'text-accent-danger'
    case 'warning': return 'text-accent-warning'
    case 'caution': return 'text-brand-sky'
    default: return 'text-white/50'
  }
}

const getSeverityBg = (severity) => {
  switch (severity) {
    case 'danger': return 'bg-accent-danger/20'
    case 'warning': return 'bg-accent-warning/20'
    case 'caution': return 'bg-brand-sky/20'
    default: return 'bg-white/10'
  }
}

const getSeverityName = (severity) => {
  switch (severity) {
    case 'danger': return '严重问题'
    case 'warning': return '一般问题'
    case 'caution': return '轻微问题'
    default: return '未知'
  }
}
</script>

<template>
  <div class="basic-report-preview">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-white">基础报告预览</h3>
      <button @click="downloadBasicReport" class="btn-secondary text-sm py-2">
        <svg class="w-4 h-4 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
            d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        下载基础报告
      </button>
    </div>
    
    <!-- 统计数据 -->
    <div class="grid grid-cols-4 gap-4 mb-6">
      <div class="glass-card p-4 text-center">
        <div class="text-2xl font-bold text-white">{{ store.statistics.totalImages }}</div>
        <div class="text-xs text-white/60 mt-1">总图片数</div>
      </div>
      <div class="glass-card p-4 text-center">
        <div class="text-2xl font-bold text-accent-danger">{{ issuesByType.danger.length }}</div>
        <div class="text-xs text-white/60 mt-1">严重问题</div>
      </div>
      <div class="glass-card p-4 text-center">
        <div class="text-2xl font-bold text-accent-warning">{{ issuesByType.warning.length }}</div>
        <div class="text-xs text-white/60 mt-1">一般问题</div>
      </div>
      <div class="glass-card p-4 text-center">
        <div class="text-2xl font-bold text-brand-sky">{{ totalIssues }}</div>
        <div class="text-xs text-white/60 mt-1">问题总数</div>
      </div>
    </div>
    
    <!-- 问题列表 -->
    <div class="space-y-4">
      <template v-for="(issues, severity) in issuesByType" :key="severity">
        <div v-if="issues.length > 0" class="glass-card p-4">
          <div class="flex items-center gap-2 mb-3">
            <div 
              class="w-3 h-3 rounded-full"
              :class="getSeverityColor(severity)"
              style="background-color: currentColor;"
            ></div>
            <h4 class="font-semibold text-white">
              {{ getSeverityName(severity) }} ({{ issues.length }})
            </h4>
          </div>
          
          <div class="space-y-2 max-h-60 overflow-y-auto">
            <div 
              v-for="(issue, index) in issues"
              :key="issue.id"
              class="flex items-start gap-3 p-2 rounded-lg"
              :class="getSeverityBg(severity)"
            >
              <div class="flex-shrink-0 w-6 h-6 rounded-full bg-white/10 flex items-center justify-center text-xs text-white">
                {{ index + 1 }}
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between gap-2">
                  <span class="font-medium text-white text-sm">{{ issue.name }}</span>
                  <span class="text-xs text-white/50 flex-shrink-0">
                    {{ (issue.confidence * 100).toFixed(0) }}%
                  </span>
                </div>
                <div class="text-xs text-white/60 mt-1">{{ issue.description }}</div>
                <div class="text-xs text-white/40 mt-1">图片: {{ issue.imageName }}</div>
              </div>
            </div>
          </div>
        </div>
      </template>
      
      <!-- 无问题提示 -->
      <div v-if="totalIssues === 0" class="glass-card p-8 text-center">
        <div class="text-4xl mb-3">✅</div>
        <div class="text-white font-semibold">未检测到问题</div>
        <div class="text-white/50 text-sm mt-1">所有图片状态良好</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 自定义滚动条 */
.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: rgba(91, 214, 255, 0.3);
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: rgba(91, 214, 255, 0.5);
}
</style>

