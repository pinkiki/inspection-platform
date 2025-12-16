<template>
  <div class="step-toolbar">
    <div class="container mx-auto px-6 py-3">
      <div class="flex items-center justify-between">
        <!-- 左侧：页面标题和说明 -->
        <div class="flex items-center gap-4">
          <div>
            <h1 class="text-xl font-bold text-gray-800">{{ title }}</h1>
            <p v-if="description" class="text-sm text-gray-600 mt-0.5">{{ description }}</p>
          </div>
        </div>

        <!-- 右侧：操作按钮 -->
        <div class="flex items-center gap-3">
          <!-- 保存进度按钮 -->
          <SaveProgressButton
            v-if="showSaveButton"
            :button-text="saveButtonText"
            :disabled="saveDisabled"
            @saved="onSaved"
          />

          <!-- 额外的操作按钮（通过插槽传入） -->
          <slot name="actions" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import SaveProgressButton from './SaveProgressButton.vue'

const props = defineProps({
  // 页面标题
  title: {
    type: String,
    required: true
  },
  // 页面描述
  description: {
    type: String,
    default: ''
  },
  // 是否显示保存按钮
  showSaveButton: {
    type: Boolean,
    default: true
  },
  // 保存按钮文字
  saveButtonText: {
    type: String,
    default: '保存进度'
  },
  // 保存按钮是否禁用
  saveDisabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['saved'])

const onSaved = () => {
  emit('saved')
}
</script>

<style scoped>
.step-toolbar {
  background: white;
  border-bottom: 1px solid #e5e7eb;
  position: sticky;
  top: 0;
  z-index: 40;
}
</style>