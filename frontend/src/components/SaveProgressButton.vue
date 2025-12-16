<template>
  <div class="save-progress-button">
    <el-dialog
      v-model="dialogVisible"
      title="保存进度"
      width="450px"
      :before-close="handleClose"
    >
      <el-form :model="form" label-width="80px">
        <el-form-item label="快照名称">
          <el-input
            v-model="form.name"
            placeholder="为快照起个名字（可选）"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="添加一些备注信息（可选）"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            @click="handleSave"
            :loading="saving"
          >
            保存进度
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 触发按钮 -->
    <el-button
      type="success"
      :icon="Bookmark"
      @click="openDialog"
      :disabled="disabled"
    >
      {{ buttonText }}
    </el-button>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Bookmark } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useProjectStore } from '../stores/project'

const props = defineProps({
  // 自定义按钮文字
  buttonText: {
    type: String,
    default: '保存进度'
  },
  // 是否禁用按钮
  disabled: {
    type: Boolean,
    default: false
  },
  // 按钮类型
  type: {
    type: String,
    default: 'success'
  },
  // 是否显示图标
  showIcon: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['saved'])

const projectStore = useProjectStore()

const dialogVisible = ref(false)
const saving = ref(false)
const form = ref({
  name: '',
  description: ''
})

// 生成默认快照名称
const generateDefaultName = () => {
  const stepName = projectStore.getStepName(projectStore.currentStep)
  const date = new Date().toLocaleDateString().replace(/\//g, '-')
  const time = new Date().toLocaleTimeString().slice(0, 5)
  return `${stepName} - ${date} ${time}`
}

const openDialog = () => {
  // 设置默认名称
  form.value.name = generateDefaultName()
  form.value.description = `保存于步骤：${projectStore.getStepName(projectStore.currentStep)}`
  dialogVisible.value = true
}

const handleClose = () => {
  form.value.name = ''
  form.value.description = ''
  dialogVisible.value = false
}

const handleSave = async () => {
  if (saving.value) return

  try {
    saving.value = true

    // 调用store方法保存快照
    await projectStore.saveSnapshotToServer({
      name: form.value.name || generateDefaultName(),
      description: form.value.description
    })

    ElMessage.success('进度保存成功！')
    handleClose()
    emit('saved')
  } catch (error) {
    console.error('保存进度失败:', error)
    ElMessage.error(error.message || '保存进度失败，请稍后重试')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.save-progress-button {
  display: inline-block;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>