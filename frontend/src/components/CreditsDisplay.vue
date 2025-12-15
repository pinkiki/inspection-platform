<script setup>
import { ref, computed } from 'vue'
import { useProjectStore } from '../stores/project'

const store = useProjectStore()
const showHistory = ref(false)

// 检查是否是管理员模式
const isAdminMode = computed(() => {
  return localStorage.getItem('adminMode') === 'true'
})

// 格式化时间
const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 获取操作类型图标
const getTypeIcon = (amount) => {
  return amount > 0 ? '+' : '-'
}

// 获取操作类型颜色
const getTypeColor = (amount) => {
  return amount > 0 ? 'text-accent-success' : 'text-accent-danger'
}

const toggleHistory = () => {
  showHistory.value = !showHistory.value
}

const closeHistory = () => {
  showHistory.value = false
}
</script>

<template>
  <div class="credits-display">
    <!-- 积分余额显示 -->
    <button 
      @click="toggleHistory"
      class="flex items-center gap-2 px-4 py-2 rounded-xl transition-all duration-200"
      :class="isAdminMode ? 'bg-accent-warning/20 hover:bg-accent-warning/30' : (store.hasLowCredits ? 'bg-accent-danger/20 hover:bg-accent-danger/30' : 'bg-base-elevated hover:bg-base-elevated')"
    >
      <svg class="w-5 h-5" :class="isAdminMode ? 'text-accent-warning' : (store.hasLowCredits ? 'text-accent-danger' : 'text-brand-sky')" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
          d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span v-if="isAdminMode" class="font-bold text-accent-warning">∞</span>
      <span v-else class="font-mono font-bold text-text-primary">{{ store.userCredits }}</span>
      <span class="text-sm text-text-secondary">{{ isAdminMode ? '管理员' : '积分' }}</span>
      <svg
        class="w-4 h-4 text-text-secondary transition-transform"
        :class="{ 'rotate-180': showHistory }"
        fill="none" 
        stroke="currentColor" 
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </button>
    
    <!-- 低积分警告 -->
    <div v-if="store.hasLowCredits" class="absolute -bottom-2 left-1/2 -translate-x-1/2 whitespace-nowrap">
      <span class="text-xs text-accent-danger">积分不足!</span>
    </div>
    
    <!-- 积分历史弹窗 -->
    <Teleport to="body">
      <div 
        v-if="showHistory"
        class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-start justify-end p-4"
        @click="closeHistory"
      >
        <div 
          class="glass-card p-6 w-96 max-h-[80vh] overflow-auto mt-16 mr-4"
          @click.stop
        >
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-bold text-text-primary">积分明细</h3>
            <button @click="closeHistory" class="text-text-secondary hover:text-text-primary">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          <!-- 当前余额 -->
          <div class="glass-card p-4 mb-4 text-center">
            <div class="text-sm text-text-secondary mb-1">当前余额</div>
            <div v-if="isAdminMode" class="text-3xl font-bold text-accent-warning">
              ∞
            </div>
            <div v-else class="text-3xl font-bold text-brand-sky font-mono">{{ store.userCredits }}</div>
            <div class="text-xs text-text-secondary mt-1">{{ isAdminMode ? '管理员模式' : '积分' }}</div>
          </div>
          
          <!-- 历史记录 -->
          <div v-if="store.creditsHistory.length > 0" class="space-y-2">
            <div class="text-sm text-text-secondary mb-2">消费记录</div>
            <div 
              v-for="record in store.creditsHistory"
              :key="record.id"
              class="flex items-center justify-between p-3 rounded-lg bg-base-elevated hover:bg-base-elevated transition-colors"
            >
              <div class="flex-1">
                <div class="text-text-primary text-sm">{{ record.reason }}</div>
                <div class="text-text-secondary text-xs mt-1">{{ formatTime(record.timestamp) }}</div>
              </div>
              <div class="flex items-center gap-3">
                <div 
                  class="font-mono font-bold"
                  :class="getTypeColor(record.amount)"
                >
                  {{ getTypeIcon(record.amount) }}{{ Math.abs(record.amount) }}
                </div>
                <div class="text-text-secondary text-xs font-mono w-12 text-right">
                  {{ record.balance }}
                </div>
              </div>
            </div>
          </div>
          
          <!-- 无记录 -->
          <div v-else class="text-center py-8 text-text-secondary">
            暂无消费记录
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.credits-display {
  position: relative;
}

/* 自定义滚动条 */
.overflow-auto::-webkit-scrollbar {
  width: 6px;
}

.overflow-auto::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 3px;
}

.overflow-auto::-webkit-scrollbar-thumb {
  background: rgba(91, 214, 255, 0.3);
  border-radius: 3px;
}

.overflow-auto::-webkit-scrollbar-thumb:hover {
  background: rgba(91, 214, 255, 0.5);
}
</style>

