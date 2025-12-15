<script setup>
import { computed } from 'vue'
import { useProjectStore } from '../stores/project'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: '确认操作'
  },
  message: {
    type: String,
    required: true
  },
  confirmText: {
    type: String,
    default: '确认'
  },
  cancelText: {
    type: String,
    default: '取消'
  },
  creditsCost: {
    type: Number,
    default: 0
  },
  type: {
    type: String,
    default: 'info', // info, warning, danger
    validator: (value) => ['info', 'warning', 'danger'].includes(value)
  }
})

const emit = defineEmits(['confirm', 'cancel', 'close'])

const store = useProjectStore()

const iconClass = computed(() => {
  switch (props.type) {
    case 'warning':
      return 'text-accent-warning'
    case 'danger':
      return 'text-accent-danger'
    default:
      return 'text-brand-sky'
  }
})

const iconBgClass = computed(() => {
  switch (props.type) {
    case 'warning':
      return 'bg-accent-warning/20'
    case 'danger':
      return 'bg-accent-danger/20'
    default:
      return 'bg-brand-sky/20'
  }
})

const canAfford = computed(() => {
  if (props.creditsCost === 0) return true
  return store.canAfford(props.creditsCost)
})

const handleConfirm = () => {
  emit('confirm')
}

const handleCancel = () => {
  emit('cancel')
  emit('close')
}

const handleClose = () => {
  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <div 
      v-if="show"
      class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      @click="handleClose"
    >
      <div 
        class="glass-card p-6 max-w-md w-full animate-fade-in"
        @click.stop
      >
        <!-- 图标 -->
        <div class="flex items-center justify-center mb-4">
          <div 
            class="w-16 h-16 rounded-full flex items-center justify-center"
            :class="iconBgClass"
          >
            <!-- Warning Icon -->
            <svg 
              v-if="type === 'warning'"
              class="w-8 h-8"
              :class="iconClass"
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            
            <!-- Danger Icon -->
            <svg 
              v-else-if="type === 'danger'"
              class="w-8 h-8"
              :class="iconClass"
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            
            <!-- Info Icon -->
            <svg 
              v-else
              class="w-8 h-8"
              :class="iconClass"
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        </div>
        
        <!-- 标题 -->
        <h3 class="text-xl font-bold text-text-primary text-center mb-3">{{ title }}</h3>

        <!-- 消息 -->
        <p class="text-text-primary text-center mb-4 whitespace-pre-line">{{ message }}</p>
        
        <!-- 积分消耗提示 -->
        <div v-if="creditsCost > 0" class="glass-card p-4 mb-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <svg class="w-5 h-5 text-brand-sky" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span class="text-text-primary text-sm">需要消耗积分</span>
            </div>
            <span class="text-brand-sky font-mono font-bold">{{ creditsCost }}</span>
          </div>
          
          <div class="flex items-center justify-between mt-2 pt-2 border-t border-line-light">
            <span class="text-text-secondary text-xs">当前余额</span>
            <span
              class="font-mono text-sm"
              :class="canAfford ? 'text-text-primary' : 'text-accent-danger'"
            >
              {{ store.userCredits }}
            </span>
          </div>
          
          <div class="flex items-center justify-between mt-1">
            <span class="text-text-secondary text-xs">操作后余额</span>
            <span 
              class="font-mono text-sm font-bold"
              :class="canAfford ? 'text-accent-success' : 'text-accent-danger'"
            >
              {{ canAfford ? store.userCredits - creditsCost : store.userCredits }}
            </span>
          </div>
          
          <!-- 积分不足警告 -->
          <div v-if="!canAfford" class="mt-3 p-2 bg-accent-danger/20 rounded-lg">
            <div class="flex items-center gap-2 text-accent-danger text-xs">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span>积分不足，无法执行此操作</span>
            </div>
          </div>
        </div>
        
        <!-- 按钮 -->
        <div class="flex items-center gap-3">
          <button 
            v-if="cancelText"
            @click="handleCancel"
            class="flex-1 py-3 px-4 rounded-xl bg-base-elevated hover:bg-base-elevated text-text-primary font-medium transition-colors"
          >
            {{ cancelText }}
          </button>
          <button 
            @click="handleConfirm"
            :disabled="!canAfford && creditsCost > 0"
            :class="[
              cancelText ? 'flex-1' : 'w-full',
              'py-3 px-4 rounded-xl font-medium transition-colors',
              canAfford || creditsCost === 0 
                ? 'bg-brand-primary hover:bg-brand-primary/80 text-white' 
                : 'bg-base-elevated text-text-secondary cursor-not-allowed'
            ]"
          >
            {{ confirmText }}
          </button>
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
</style>

