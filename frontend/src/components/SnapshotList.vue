<template>
  <div class="snapshot-list">
    <!-- 头部 -->
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-gray-800">我的步骤快照</h3>
      <el-button
        type="primary"
        :icon="Refresh"
        size="small"
        @click="refreshSnapshots"
        :loading="loading"
      >
        刷新
      </el-button>
    </div>

    <!-- 快照列表 -->
    <div v-if="loading && (!snapshots || snapshots.length === 0)" class="text-center py-8">
      <el-icon class="is-loading" size="32">
        <Loading />
      </el-icon>
      <p class="mt-2 text-gray-500">加载中...</p>
    </div>

    <div v-else-if="!snapshots || snapshots.length === 0" class="text-center py-8">
      <el-empty
        description="暂无步骤快照"
        :image-size="120"
      >
        <template #image>
          <el-icon size="80" color="#d3d3d3">
            <Document />
          </el-icon>
        </template>
        <p class="text-gray-500 text-sm mt-2">
          在主流程中点击"保存进度"按钮来创建快照
        </p>
      </el-empty>
    </div>

    <div v-else class="space-y-3">
      <transition-group name="list">
        <div
          v-for="snapshot in snapshots"
          :key="snapshot.id"
          class="snapshot-card"
        >
          <!-- 快照信息 -->
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-1">
                <span class="snapshot-name">
                  {{ snapshot.name || `步骤${snapshot.step_index + 1}：${snapshot.stepName}` }}
                </span>
                <el-tag
                  :type="getStepTagType(snapshot.step_index)"
                  size="small"
                >
                  {{ snapshot.stepName }}
                </el-tag>
              </div>

              <p class="snapshot-time">
                {{ formatTime(snapshot.timestamp) }}
              </p>

              <!-- 步骤进度条 -->
              <div class="step-progress-mini mt-2">
                <div
                  class="progress-bar"
                  :style="{ width: `${(snapshot.step / 6) * 100}%` }"
                />
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="flex items-center gap-2">
              <el-tooltip
                content="恢复此快照"
                placement="top"
              >
                <el-button
                  type="primary"
                  :icon="RefreshRight"
                  size="small"
                  circle
                  @click="handleRestore(snapshot)"
                  :loading="restoringId === snapshot.id"
                />
              </el-tooltip>

              <el-tooltip
                content="删除快照"
                placement="top"
              >
                <el-button
                  type="danger"
                  :icon="Delete"
                  size="small"
                  circle
                  @click="handleDelete(snapshot)"
                  :loading="deletingId === snapshot.id"
                />
              </el-tooltip>
            </div>
          </div>
        </div>
      </transition-group>
    </div>

  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh,
  Loading,
  Document,
  RefreshRight,
  Delete
} from '@element-plus/icons-vue'
import { useProjectStore } from '../stores/project'

const router = useRouter()
const projectStore = useProjectStore()

// 接收props和emit
const props = defineProps({
  snapshotList: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['deleted', 'refresh', 'restored', 'restore-request'])

const loading = ref(false)
const snapshots = ref([])
const restoringId = ref(null)
const deletingId = ref(null)

// 加载快照列表
const loadSnapshots = async () => {
  loading.value = true
  try {
    await projectStore.loadSnapshotsFromServer()
    snapshots.value = projectStore.stepSnapshots
  } catch (error) {
    console.error('加载快照失败:', error)
    ElMessage.error('加载快照列表失败')
  } finally {
    loading.value = false
  }
}

// 刷新快照列表
const refreshSnapshots = () => {
  emit('refresh')
}

// 获取步骤标签类型
const getStepTagType = (step) => {
  if (step <= 2) return 'info'      // 上传、分析
  if (step <= 4) return 'warning'   // 模板、审核
  return 'success'                  // 进阶、导出
}

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return ''

  // 处理数据库返回的时间格式
  let date
  if (timestamp.includes('T')) {
    // ISO格式时间，直接解析
    date = new Date(timestamp)
  } else {
    // 可能是数据库格式，添加时区信息
    date = new Date(timestamp + 'Z')
  }

  // 确保时间有效
  if (isNaN(date.getTime())) {
    return timestamp
  }

  const now = new Date()
  const diff = now - date

  // 如果是今天
  if (diff < 24 * 60 * 60 * 1000 && diff >= 0) {
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  // 其他日期
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 处理恢复快照 - 发送请求事件到父组件
const handleRestore = (snapshot) => {
  emit('restore-request', snapshot)
}

// 处理删除快照
const handleDelete = async (snapshot) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除快照"${snapshot.name || `步骤${snapshot.step_index + 1}：${snapshot.stepName}`}"吗？`,
      '删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    deletingId.value = snapshot.id

    // 调用store方法删除快照
    await projectStore.deleteSnapshotFromServer(snapshot.id)

    ElMessage.success('快照已删除')

    // 通知父组件删除成功
    emit('deleted', snapshot.id)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除快照失败:', error)
      ElMessage.error(error.message || '删除快照失败')
    }
  } finally {
    deletingId.value = null
  }
}

// 监听props变化，更新snapshots
watch(() => props.snapshotList, (newList) => {
  snapshots.value = newList || []
}, { immediate: true })
</script>

<style scoped>
.snapshot-list {
  background: white;
  border-radius: 8px;
  padding: 20px;
}

.snapshot-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.3s ease;
  background: white;
}

.snapshot-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
}

.snapshot-name {
  font-weight: 500;
  color: #1f2937;
}

.snapshot-time {
  font-size: 13px;
  color: #6b7280;
}

.step-progress-mini {
  width: 100%;
  height: 4px;
  background: #f3f4f6;
  border-radius: 2px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #10b981);
  border-radius: 2px;
  transition: width 0.3s ease;
}

/* 列表动画 */
.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}

.list-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.list-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

:deep(.el-alert__content) {
  font-size: 14px;
}
</style>