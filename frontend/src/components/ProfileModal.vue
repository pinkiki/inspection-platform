<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useProjectStore, CREDIT_PRICES } from '../stores/project'
import ConfirmDialog from './ConfirmDialog.vue'
import SnapshotList from './SnapshotList.vue'

const router = useRouter()
const store = useProjectStore()

const loading = ref(false)

// 用户信息
const userInfo = ref({
  name: '用户',
  email: 'user@example.com',
  avatar: null,
  joinDate: new Date().toISOString().split('T')[0],
  totalProjects: 0,
  totalReports: 0,
  lastLogin: new Date().toLocaleString()
})

// 积分信息
const creditInfo = ref({
  current: 10000,
  totalUsed: 0,
  totalEarned: 0,
  level: '普通用户',
  nextLevel: null
})

// 步骤快照
const stepSnapshots = ref([])

// 恢复快照对话框
const showRestoreDialog = ref(false)
const selectedSnapshot = ref(null)
const restoring = ref(false)


// 积分明细分页
const creditPagination = ref({
  currentPage: 1,
  pageSize: 5,
  totalRecords: 0,
  totalPages: 0,
  hasPrev: false,
  hasNext: false
})
const creditRecords = ref([])

// 获取积分历史记录
const fetchCreditHistory = async (page = 1) => {
  try {
    const response = await fetch(`/api/user/credit-history?page=${page}&page_size=${creditPagination.value.pageSize}`)
    if (response.ok) {
      const data = await response.json()
      creditRecords.value = data.records

      // 更新分页数据，确保字段名正确映射
      creditPagination.value = {
        currentPage: data.pagination.current_page,
        pageSize: data.pagination.page_size,
        totalRecords: data.pagination.total_records,
        totalPages: data.pagination.total_pages,
        hasPrev: data.pagination.has_prev,
        hasNext: data.pagination.has_next
      }
    }
  } catch (error) {
    console.error('获取积分历史失败:', error)
  }
}

// 获取用户信息
const fetchUserProfile = async () => {
  try {
    loading.value = true
    const response = await fetch('/api/user/profile')
    if (response.ok) {
      const data = await response.json()
      userInfo.value = {
        name: data.user_info.name,
        email: data.user_info.email,
        avatar: data.user_info.avatar,
        joinDate: data.user_info.join_date,
        totalProjects: data.user_info.total_projects,
        totalReports: data.user_info.total_reports,
        lastLogin: data.user_info.last_login
      }
      // 积分信息优先使用store中的数据，确保一致性
      creditInfo.value = {
        current: store.userCredits || data.current_credits,
        totalUsed: data.total_used,
        totalEarned: data.total_earned,
        level: data.level,
        nextLevel: data.next_level_info
      }

      // 更新store中的当前积分
      store.userCredits = data.current_credits

      // 设置步骤快照
      stepSnapshots.value = data.step_snapshots || []

      // 获取积分历史记录
      await fetchCreditHistory(1)
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
    // 如果API失败，使用store中的数据作为后备
    userInfo.value = {
      name: store.currentUser?.name || '用户',
      email: store.currentUser?.email || 'user@example.com',
      avatar: store.currentUser?.avatar || null,
      joinDate: store.currentUser?.joinDate || new Date().toISOString().split('T')[0],
      totalProjects: store.userStats?.totalProjects || 0,
      totalReports: store.userStats?.totalReports || 0,
      lastLogin: store.userStats?.lastLogin || new Date().toLocaleString()
    }
    creditInfo.value = {
      current: store.userCredits,
      totalUsed: store.creditHistory
        .filter(record => record.type === 'spend')
        .reduce((sum, record) => sum + Math.abs(record.amount), 0),
      totalEarned: store.creditHistory
        .filter(record => record.type === 'earn')
        .reduce((sum, record) => sum + record.amount, 0),
      level: store.getUserLevel(),
      nextLevel: store.getNextLevel()
    }
  } finally {
    loading.value = false
  }
}


// 关闭
const close = () => {
  store.showProfileModal = false
}

// 处理快照删除
const handleSnapshotDeleted = (snapshotId) => {
  // 从本地快照列表中移除
  stepSnapshots.value = stepSnapshots.value.filter(s => s.id !== snapshotId)
}

// 处理快照刷新
const handleSnapshotRefresh = async () => {
  await fetchUserProfile()
}

// 处理快照恢复请求 - 打开恢复确认对话框
const handleSnapshotRestoreRequest = (snapshot) => {
  selectedSnapshot.value = snapshot
  showRestoreDialog.value = true
}

// 确认恢复快照
const confirmRestore = async () => {
  if (!selectedSnapshot.value) return

  // 检查积分是否足够
  if (store.userCredits < 20) {
    ElMessage.error('积分不足，恢复快照需要20积分')
    return
  }

  restoring.value = true

  try {
    // 调用store方法恢复快照
    const result = await store.restoreSnapshotFromServer(
      selectedSnapshot.value.id
    )

    // 显示成功消息，包含积分信息
    const creditsDeducted = result.data?.credits_deducted || 20
    const balanceAfter = result.data?.balance_after
    const message = balanceAfter
      ? `快照恢复成功！已扣除${creditsDeducted}积分，当前余额：${balanceAfter}积分`
      : '快照恢复成功！'

    ElMessage({
      message,
      type: 'success',
      duration: 5000
    })

    // 关闭对话框
    showRestoreDialog.value = false

    // 更新store中的积分余额
    if (balanceAfter !== undefined) {
      store.userCredits = balanceAfter
    }

    // 刷新用户信息以获取最新数据
    await fetchUserProfile()

    // 跳转到对应步骤
    if (result.data?.stepRoute) {
      router.push(result.data.stepRoute)
    }
  } catch (error) {
    console.error('恢复快照失败:', error)

    // 处理积分不足的错误
    if (error.message.includes('积分不足') || error.message.includes('Payment Required')) {
      ElMessage.error('积分不足，恢复快照需要20积分')
    } else {
      ElMessage.error(error.message || '恢复快照失败')
    }
  } finally {
    restoring.value = false
  }
}

// 处理快照恢复（保留兼容性）
const handleSnapshotRestored = async (data) => {
  // 更新store中的积分余额
  if (data.balanceAfter !== undefined) {
    store.userCredits = data.balanceAfter
  }

  // 刷新用户信息以获取最新的积分历史
  await fetchUserProfile()
}

// 分页控制函数
const handlePageChange = (page) => {
  fetchCreditHistory(page)
}

const handleSizeChange = (size) => {
  creditPagination.value.pageSize = size
  fetchCreditHistory(1) // 切换每页大小时回到第一页
}

// 组件挂载时获取用户信息
onMounted(() => {
  if (store.showProfileModal) {
    fetchUserProfile()
  }
})

// 监听模态框显示状态
watch(() => store.showProfileModal, (newVal) => {
  if (newVal) {
    fetchUserProfile()
  }
})

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return '未知时间'

  // 处理数据库返回的时间字符串
  // 数据库存储的是UTC时间，需要正确解析为UTC时间
  const date = new Date(timestamp + 'Z') // 添加'Z'表示这是UTC时间
  const now = new Date()

  // 确保时间有效
  if (isNaN(date.getTime())) {
    return timestamp
  }

  // 计算时间差（毫秒）
  const diff = now - date

  // 如果是未来的时间，直接显示完整时间
  if (diff < 0) {
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  // 计算相对时间
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  // 根据时间差显示不同的格式
  if (minutes < 1) {
    return '刚刚'
  } else if (minutes < 60) {
    return `${minutes}分钟前`
  } else if (hours < 24) {
    return `${hours}小时前`
  } else if (days < 7) {
    return `${days}天前`
  } else if (date.getFullYear() === now.getFullYear()) {
    // 今年内，显示月日时间
    return date.toLocaleString('zh-CN', {
      month: 'numeric',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } else {
    // 跨年，显示完整日期
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    })
  }
}

// 格式化积分使用记录
const formatCreditRecord = (record) => {
  const typeText = record.type === 'spend' ? '消费' : '获得'
   const amountText = record.type === 'spend' ? 
    - `-${record.amount}` : `+${record.amount}`
  return { typeText, amountText }
}
</script>

<template>
  <!-- 个人信息模态框 -->
  <div v-if="store.showProfileModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
    <!-- 背景遮罩 -->
    <div
      class="absolute inset-0 bg-black/50 backdrop-blur-sm"
      @click="close"
    ></div>

    <!-- 模态框内容 -->
    <div class="glass-card p-8 max-w-4xl w-full max-h-[90vh] overflow-auto relative">
      <!-- 关闭按钮 -->
      <button
        @click="close"
        class="absolute top-4 right-4 w-10 h-10 rounded-xl text-text-secondary hover:text-text-primary hover:bg-base-elevated transition-colors flex items-center justify-center"
      >
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      <!-- 标题 -->
      <h2 class="text-2xl font-bold text-text-primary mb-6 flex items-center gap-3">
        <svg class="w-8 h-8 text-brand-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
        个人信息
      </h2>

      <!-- 加载状态 -->
      <div v-if="loading" class="flex justify-center py-12">
        <div class="animate-spin rounded-full h-8 w-8 border-2 border-brand-primary border-t-transparent"></div>
      </div>

      <div v-else class="grid grid-cols-3 gap-6">
        <!-- 用户基本信息 -->
        <div class="col-span-1">
          <div class="glass-card p-6">
            <h3 class="text-lg font-semibold text-text-primary mb-4">基本信息</h3>

            <!-- 头像 -->
            <div class="flex justify-center mb-4">
              <div class="w-24 h-24 rounded-full bg-gradient-to-br from-brand-primary to-brand-sky flex items-center justify-center">
                <span v-if="!userInfo.avatar" class="text-3xl font-bold text-white">
                  {{ userInfo.name.charAt(0).toUpperCase() }}
                </span>
                <img v-else :src="userInfo.avatar" :alt="userInfo.name" class="w-full h-full rounded-full object-cover">
              </div>
            </div>

            <!-- 用户名 -->
            <div class="text-center mb-4">
              <h4 class="text-xl font-bold text-text-primary">{{ userInfo.name }}</h4>
              <p class="text-sm text-text-secondary">{{ userInfo.email }}</p>
            </div>

            <!-- 详细信息 -->
            <div class="space-y-3">
              <div class="kv-row">
                <span class="label">注册时间</span>
                <span class="value">{{ userInfo.joinDate }}</span>
              </div>
              <div class="kv-row">
                <span class="label">总项目数</span>
                <span class="value">{{ userInfo.totalProjects }}</span>
              </div>
              <div class="kv-row">
                <span class="label">生成报告</span>
                <span class="value">{{ userInfo.totalReports }}</span>
              </div>
              <div class="kv-row">
                <span class="label">上次登录</span>
                <span class="value text-xs">{{ userInfo.lastLogin }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 积分信息和步骤快照 -->
        <div class="col-span-2 space-y-6">
          <!-- 积分信息 -->
          <div class="glass-card p-6">
            <h3 class="text-lg font-semibold text-text-primary mb-4">积分信息</h3>

            <!-- 积分概览 -->
            <div class="grid grid-cols-4 gap-4 mb-6">
              <div class="text-center">
                <div class="text-3xl font-bold text-brand-primary">{{ creditInfo.current }}</div>
                <div class="text-sm text-text-secondary">当前积分</div>
              </div>
              <div class="text-center">
                <div class="text-2xl font-bold text-accent-danger">{{ creditInfo.totalUsed }}</div>
                <div class="text-sm text-text-secondary">累计消费</div>
              </div>
              <div class="text-center">
                <div class="text-2xl font-bold text-accent-success">{{ creditInfo.totalEarned }}</div>
                <div class="text-sm text-text-secondary">累计获得</div>
              </div>
              <div class="text-center">
                <div class="text-2xl font-bold text-brand-sky">{{ creditInfo.level }}</div>
                <div class="text-sm text-text-secondary">用户等级</div>
              </div>
            </div>

            <!-- 积分等级进度条 -->
            <div v-if="creditInfo.nextLevel" class="mb-4">
              <div class="flex justify-between text-sm mb-2">
                <span class="text-text-secondary">升级进度</span>
                <span class="text-text-secondary">{{ creditInfo.level }} → {{ creditInfo.nextLevel.level }}</span>
              </div>
              <div class="h-2 bg-base-elevated rounded-full overflow-hidden">
                <div
                  class="h-full bg-gradient-to-r from-brand-primary to-brand-sky transition-all duration-300"
                  :style="{ width: `${creditInfo.nextLevel.progress}%` }"
                ></div>
              </div>
              <div class="text-xs text-text-secondary mt-1">
                还需要 {{ creditInfo.nextLevel.creditsNeeded }} 积分升级
              </div>
            </div>
          </div>

          <!-- 积分历史记录 -->
          <div class="glass-card p-6">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-semibold text-text-primary">积分明细</h3>
              <div class="text-sm text-text-secondary">
                共 {{ creditPagination.totalRecords }} 条记录，第 {{ creditPagination.currentPage }}/{{ creditPagination.totalPages }} 页
              </div>
            </div>

            <div v-if="creditRecords.length === 0" class="text-center py-12 text-text-secondary">
              <svg class="w-16 h-16 mx-auto mb-3 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
              </svg>
              暂无积分记录
            </div>

            <!-- 表格 -->
            <div v-else class="overflow-hidden rounded-lg border border-line-light">
              <table class="w-full">
                <thead>
                  <tr class="bg-base-elevated border-b border-line-light">
                    <th class="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">类型</th>
                    <th class="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">说明</th>
                    <th class="px-4 py-3 text-right text-xs font-semibold text-text-secondary uppercase tracking-wider">积分变动</th>
                    <th class="px-4 py-3 text-right text-xs font-semibold text-text-secondary uppercase tracking-wider">余额</th>
                    <th class="px-4 py-3 text-right text-xs font-semibold text-text-secondary uppercase tracking-wider">时间</th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-line-light">
                  <tr
                    v-for="record in creditRecords"
                    :key="record.id"
                    class="hover:bg-base-elevated/50 transition-colors"
                  >
                    <!-- 类型标签 -->
                    <td class="px-4 py-3 whitespace-nowrap">
                      <span
                        class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                        :class="record.type === 'earn'
                          ? 'bg-accent-success/10 text-accent-success'
                          : 'bg-accent-danger/10 text-accent-danger'"
                      >
                        {{ record.type === 'earn' ? '获得' : '消费' }}
                      </span>
                    </td>

                    <!-- 说明 -->
                    <td class="px-4 py-3 text-sm text-text-primary">
                      {{ record.reason }}
                    </td>

                    <!-- 积分变动 -->
                    <td class="px-4 py-3 whitespace-nowrap text-right">
                      <span
                        class="text-sm font-bold font-mono"
                        :class="record.type === 'earn' ? 'text-accent-success' : 'text-accent-danger'"
                      >
                         {{ record.type === 'earn' ? '+' : '-' }}{{ record.amount }}
                      </span>
                    </td>

                    <!-- 余额 -->
                    <td class="px-4 py-3 whitespace-nowrap text-right">
                      <span class="text-sm font-mono text-text-primary">
                        {{ record.balance_after }}
                      </span>
                    </td>

                    <!-- 时间 -->
                    <td class="px-4 py-3 whitespace-nowrap text-right text-xs text-text-secondary">
                      <span :title="record.timestamp">
                        {{ formatTime(record.timestamp) }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>

              <!-- 分页器 -->
              <div v-if="creditRecords.length > 0" class="px-4 py-3 bg-base-elevated border-t border-line-light">
                <div class="flex items-center justify-between">
                  <div class="text-sm text-text-secondary">
                    显示 {{ (creditPagination.currentPage - 1) * creditPagination.pageSize + 1 }}-{{ Math.min(creditPagination.currentPage * creditPagination.pageSize, creditPagination.totalRecords) }} 条，共 {{ creditPagination.totalRecords }} 条
                  </div>
                  <el-pagination
                    v-if="creditPagination.totalPages > 1"
                    v-model:current-page="creditPagination.currentPage"
                    :page-size="creditPagination.pageSize"
                    :total="creditPagination.totalRecords"
                    layout="prev, pager, next"
                    :small="false"
                    @current-change="handlePageChange"
                    background
                    class="pagination-right"
                  />
                </div>
              </div>
            </div>
          </div>

          <!-- 步骤快照 -->
          <div class="glass-card p-6">
            <SnapshotList
              :snapshot-list="stepSnapshots"
              @deleted="handleSnapshotDeleted"
              @refresh="handleSnapshotRefresh"
              @restored="handleSnapshotRestored"
              @restore-request="handleSnapshotRestoreRequest"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 恢复快照确认对话框 -->
    <el-dialog
      v-model="showRestoreDialog"
      title="恢复步骤快照"
      width="450px"
      :close-on-click-modal="false"
      :append-to-body="true"
      class="restore-snapshot-dialog"
    >
      <div class="space-y-4">
        <!-- 警告信息 -->
        <el-alert
          type="warning"
          :closable="false"
          show-icon
        >
          <div class="space-y-1">
            <p>⚠️ 恢复快照将替换当前的所有进度，此操作不可撤销</p>
            <p class="font-semibold text-orange-600">💰 恢复快照需要消耗 20 积分</p>
          </div>
        </el-alert>

        <!-- 积分显示 -->
        <div class="bg-orange-50 border border-orange-200 rounded-lg p-3">
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600">当前积分余额：</span>
            <span class="text-lg font-bold text-orange-600">{{ store.userCredits }} 积分</span>
          </div>
        </div>

        <!-- 快照信息 -->
        <div v-if="selectedSnapshot" class="bg-gray-50 rounded-lg p-4">
          <h4 class="font-semibold mb-3">快照信息</h4>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span class="text-gray-600">快照名称：</span>
              <span class="font-medium">{{ selectedSnapshot.name || `步骤${selectedSnapshot.step_index + 1}：${selectedSnapshot.stepName}` }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">保存步骤：</span>
              <span class="font-medium">{{ selectedSnapshot.stepName }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">保存时间：</span>
              <span class="font-medium">{{ formatTime(selectedSnapshot.timestamp) }}</span>
            </div>
          </div>
        </div>

        <!-- 确认提示 -->
        <p class="text-sm text-gray-700 bg-blue-50 border border-blue-200 rounded-lg p-3">
          <strong>请确认：</strong>您将要花费 20 积分恢复此快照，恢复后将无法撤销此操作。
        </p>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showRestoreDialog = false">取消</el-button>
          <el-button
            type="primary"
            @click="confirmRestore"
            :loading="restoring"
            :disabled="store.userCredits < 20"
          >
            确认恢复 (消耗20积分)
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.kv-row {
  @apply flex justify-between gap-3 px-3 py-2.5 rounded-xl text-sm;
  border: 1px solid var(--line-light);
  background: rgba(245,245,245,0.5);
}

.kv-row .label {
  color: var(--text-secondary);
}

.kv-row .value {
  @apply font-mono font-bold;
  color: var(--text-primary);
}

.pagination-right {
  margin-left: auto;
}

/* Element Plus 分页器样式 */
:deep(.el-pagination) {
  --el-pagination-button-bg-color: rgba(255,255,255,0.8);
  --el-pagination-button-color: var(--text-primary);
  --el-pagination-bg-color: transparent;
  --el-pagination-hover-color: var(--brand-primary);
}

:deep(.el-pagination .el-pager li) {
  background: rgba(255,255,255,0.8);
  border: 1px solid var(--line-light);
  margin: 0 2px;
  border-radius: 4px;
}

:deep(.el-pagination .el-pager li.is-active) {
  background: var(--brand-primary);
  color: white;
  border-color: var(--brand-primary);
}

:deep(.el-pagination .btn-prev),
:deep(.el-pagination .btn-next) {
  background: rgba(255,255,255,0.8);
  border: 1px solid var(--line-light);
  border-radius: 4px;
}

:deep(.el-pagination .btn-prev:hover),
:deep(.el-pagination .btn-next:hover) {
  background: var(--brand-primary);
  color: white;
  border-color: var(--brand-primary);
}

/* 恢复快照对话框样式 */
.restore-snapshot-dialog :deep(.el-dialog) {
  border-radius: 12px;
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