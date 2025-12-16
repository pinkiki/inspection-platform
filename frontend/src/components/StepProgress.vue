<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useProjectStore, CREDIT_PRICES } from '../stores/project'
import ConfirmDialog from './ConfirmDialog.vue'
import { Camera } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const store = useProjectStore()

const showReanalysisConfirm = ref(false)
const showRestartWarning = ref(false)
const pendingNavigation = ref(null)

const steps = [
  { id: 1, name: '图像上传', path: '/', icon: 'upload' },
  { id: 2, name: '场景分析', path: '/analysis', icon: 'search' },
  { id: 3, name: '报告模板', path: '/template', icon: 'template' },
  { id: 4, name: '识别审查', path: '/review', icon: 'check' },
  { id: 5, name: '进阶报告', path: '/advanced', icon: 'cube' },
  { id: 6, name: '报告导出', path: '/export', icon: 'download' }
]

const currentStepId = computed(() => route.meta?.step || 1)

const getStepStatus = (stepId) => {
  if (stepId < currentStepId.value) return 'completed'
  if (stepId === currentStepId.value) return 'active'
  return 'pending'
}

const canNavigate = (stepId) => {
  // 只能导航到当前步骤或之前的步骤
  // return stepId <= store.currentStep
  // 只能导航到已完成的步骤
   return stepId < currentStepId.value
}

const navigateToStep = (step) => {
  if (!canNavigate(step.id)) return

  // 特殊处理：从导出步骤（步骤6）返回到关键步骤（1-3）
  if (currentStepId.value === 6 && step.id <= 3) {
    // 返回到上传、场景分析、报告模板需要确认
    pendingNavigation.value = step
    showRestartWarning.value = true
    return
  }

  // 特殊处理：从后续步骤返回场景分析
  if (step.id === 2 && currentStepId.value > 2 && currentStepId.value < 6 && store.analysisResult) {
    // 已经有场景分析结果，且是从后续步骤返回，需要确认
    showReanalysisConfirm.value = true
    return
  }

  // 直接导航
  router.push(step.path)
}

// 确认返回���景分析
const confirmBackToAnalysis = () => {
  // 扣除积分
  const success = store.deductCredits(CREDIT_PRICES.SCENE_REANALYSIS, '返回重新选择场景')

  if (success) {
    // 清除相关数据
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

// 确认重启
const confirmRestart = () => {
  if (!pendingNavigation.value) return

  // 清除所有处理结果
  store.resetDataLoadedFlag()
  store.setDetectionResults([])
  store.setAdvancedData(null)
  store.setAdvancedProcessed(false)
  store.setPaidTemplateCredits(0)
  store.resetProcessingProgress()

  // 根据返回的步骤清除相应数据
  if (pendingNavigation.value.id <= 2) {
    // 返回到上传或场景分析，清除分析结果
    store.setAnalysisResult(null)
    store.setSelectedTemplate(null)
  } else if (pendingNavigation.value.id === 3) {
    // 返回到模板选择，清除模板选择
    store.setSelectedTemplate(null)
  }

  showRestartWarning.value = false
  router.push(pendingNavigation.value.path)
  pendingNavigation.value = null
}

// 取消重启
const cancelRestart = () => {
  showRestartWarning.value = false
  pendingNavigation.value = null
}

// 手动保存快照
const manualSaveSnapshot = async (stepId) => {
  try {
    // 获取当前路由对应的步骤信息
    const step = steps.find(s => s.id === stepId)
    if (!step) {
      ElMessage.error('无法确定当前步骤')
      return
    }

    // 使用当前路由的步骤ID和名称
    const stepName = step.name
    const stepIndex = stepId - 1 // 转换为 0-based

    // 使用新的API方法保存快照
    await store.saveSnapshotToServer({
      name: `步骤${stepId}：${stepName} 快速保存`,
      description: `在步骤${stepName}手动保存的进度`,
      stepIndex: stepIndex,
      stepRoute: step.path
    })

    ElMessage.success(`进度保存成功！快照：步骤${stepId}：${stepName}`)
  } catch (error) {
    console.error('保存快照失败:', error)
    ElMessage.error(error.message || '保存进度失败，请稍后重试')
  }
}

// 监听步骤变化，自动保存快照
watch(currentStepId, (newStep, oldStep) => {
  if (newStep > oldStep && newStep > 1) {
    // 只在前进到第2步及之后时自动保存快照
    store.autoSaveSnapshot()
  }
}, { immediate: false })


</script>

<template>
  <div class="step-progress-bar">
    <div class="container mx-auto px-6 py-4">
      <div class="flex items-center justify-between">
        <div 
          v-for="(step, index) in steps" 
          :key="step.id"
          class="flex items-center"
        >
          <!-- 步骤指示器 -->
          <button
            @click="navigateToStep(step)"
            :disabled="!canNavigate(step.id)"
            class="step-btn"
            :class="{ 'cursor-not-allowed opacity-60': !canNavigate(step.id) }"
          >
            <!-- 圆形指示器 -->
            <div 
              class="step-indicator"
              :class="getStepStatus(step.id)"
            >
              <!-- 完成图标 -->
              <svg v-if="getStepStatus(step.id) === 'completed'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              <!-- 步骤数字 -->
              <span v-else>{{ step.id }}</span>
            </div>
            
            <!-- 步骤名称和保存按钮 -->
            <div class="flex items-center gap-2">
              <span
                class="step-name"
                :class="{
                  'active': getStepStatus(step.id) === 'active',
                  'completed': getStepStatus(step.id) === 'completed',
                  'pending': getStepStatus(step.id) === 'pending'
                }"
              >
                {{ step.name }}
              </span>

              <!-- 保存按钮 - 只在当前激活步骤显示 -->
              <button
                v-if="getStepStatus(step.id) === 'active'"
                @click.stop="manualSaveSnapshot(step.id)"
                class="save-btn"
                title="保存当前进度"
              >
                <el-icon size="14">
                  <Camera />
                </el-icon>
              </button>
            </div>
          </button>
          
          <!-- 连接线 -->
          <div 
            v-if="index < steps.length - 1"
            class="step-line"
            :class="{
              'completed': getStepStatus(step.id) === 'completed',
              'active': getStepStatus(step.id) === 'active',
              'pending': getStepStatus(step.id) === 'pending'
            }"
          />
        </div>
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

    <!-- 重启项目警告对话框 -->
    <ConfirmDialog
      :show="showRestartWarning"
      title="重启项目确认"
      message="返回到此步骤将清除所有处理结果（包括识别结果、进阶报告等），需要重新开始整个流程并重新计费。&#10;&#10;此操作不可撤销，是否确认？"
      :credits-cost="0"
      confirm-text="确认重启"
      cancel-text="取消"
      type="danger"
      @confirm="confirmRestart"
      @cancel="cancelRestart"
      @close="cancelRestart"
    />
  </div>
</template>

<style scoped>
.step-progress-bar {
  border-bottom: 1px solid var(--line-light);
  background: rgba(255,255,255,0.9);
  backdrop-filter: blur(8px);
}

.step-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  transition: all 0.18s ease;
}


.step-name {
  font-size: 13px;
  font-weight: 500;
  transition: color 0.2s;
}

.step-name.active {
  color: var(--text);
}

.step-name.completed {
  color: var(--good);
}

.step-name.pending {
  color: var(--muted);
  opacity: 0.6;
}

.step-line {
  flex: 1;
  height: 2px;
  margin: 0 16px;
  min-width: 40px;
  max-width: 80px;
  border-radius: 999px;
  transition: all 0.3s ease;
}

.step-line.completed {
  background: var(--good);
}

.step-line.active {
  background: linear-gradient(90deg, var(--brand), rgba(16,35,117,0.3));
}

.step-line.pending {
  background: var(--line-light);
}

.save-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
  border-radius: 6px;
  background: transparent;
  border: 1px solid rgba(16,35,117,0.2);
  color: var(--brand-muted);
  transition: all 0.2s ease;
  cursor: pointer;
  opacity: 0.7;
}

.save-btn:hover {
  background: rgba(16,35,117,0.1);
  color: var(--brand-primary);
  border-color: rgba(16,35,117,0.4);
  opacity: 1;
  transform: scale(1.1);
}

.save-btn:active {
  transform: scale(1);
}

.step-name.completed ~ .save-btn:hover {
  border-color: rgba(111,188,206,0.4);
  color: var(--good);
}

.step-name.completed ~ .save-btn:hover {
  background: rgba(111,188,206,0.1);
}
</style>

