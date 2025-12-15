<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'

const props = defineProps({
  imageSrc: {
    type: String,
    required: true
  },
  issues: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['save', 'cancel'])

// 问题类型选项
const issueTypes = [
  { type: 'crack', name: '裂缝', severity: 'danger' },
  { type: 'stain', name: '污渍', severity: 'warning' },
  { type: 'damage', name: '破损', severity: 'danger' },
  { type: 'corrosion', name: '锈蚀', severity: 'warning' },
  { type: 'deformation', name: '变形', severity: 'caution' },
  { type: 'other', name: '其他', severity: 'warning' }
]

// 本地标注数据（深拷贝）
const localIssues = ref([])

// 容器和图片引用
const containerRef = ref(null)
const imageRef = ref(null)

// 图片尺寸
const imageSize = reactive({ width: 0, height: 0, naturalWidth: 0, naturalHeight: 0 })

// 当前选中的标注
const selectedIssueId = ref(null)

// 拖拽状态
const dragState = reactive({
  isDragging: false,
  mode: null, // 'create', 'move', 'resize'
  startX: 0,
  startY: 0,
  currentX: 0,
  currentY: 0,
  resizeHandle: null, // 'nw', 'ne', 'sw', 'se'
  originalBbox: null
})

// 新建标注的临时数据
const newBox = reactive({
  x: 0,
  y: 0,
  width: 0,
  height: 0
})

// 编辑中的问题详情
const editingIssue = ref(null)

// 初始化
onMounted(() => {
  // 深拷贝初始数据
  localIssues.value = JSON.parse(JSON.stringify(props.issues))
  
  // 监听图片加载
  if (imageRef.value) {
    imageRef.value.onload = updateImageSize
  }
  
  // 监听窗口大小变化
  window.addEventListener('resize', updateImageSize)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateImageSize)
})

// 更新图片尺寸
const updateImageSize = () => {
  if (imageRef.value) {
    imageSize.width = imageRef.value.clientWidth
    imageSize.height = imageRef.value.clientHeight
    imageSize.naturalWidth = imageRef.value.naturalWidth
    imageSize.naturalHeight = imageRef.value.naturalHeight
  }
}

// 计算选中的问题
const selectedIssue = computed(() => {
  return localIssues.value.find(i => i.id === selectedIssueId.value)
})

// 获取鼠标相对于图片的百分比位置
const getRelativePosition = (e) => {
  if (!containerRef.value || !imageRef.value) return { x: 0, y: 0 }
  
  const rect = imageRef.value.getBoundingClientRect()
  const x = ((e.clientX - rect.left) / rect.width) * 100
  const y = ((e.clientY - rect.top) / rect.height) * 100
  
  return {
    x: Math.max(0, Math.min(100, x)),
    y: Math.max(0, Math.min(100, y))
  }
}

// 检查点击是否在某个标注框内
const findIssueAtPosition = (x, y) => {
  return localIssues.value.find(issue => {
    const bbox = issue.bbox
    return x >= bbox.x && x <= bbox.x + bbox.width &&
           y >= bbox.y && y <= bbox.y + bbox.height
  })
}

// 检查是否点击在调整手柄上
const findResizeHandle = (x, y, issue) => {
  if (!issue) return null
  
  const bbox = issue.bbox
  const handleSize = 3 // 手柄大小（百分比）
  
  const handles = [
    { name: 'nw', x: bbox.x, y: bbox.y },
    { name: 'ne', x: bbox.x + bbox.width, y: bbox.y },
    { name: 'sw', x: bbox.x, y: bbox.y + bbox.height },
    { name: 'se', x: bbox.x + bbox.width, y: bbox.y + bbox.height }
  ]
  
  for (const handle of handles) {
    if (Math.abs(x - handle.x) <= handleSize && Math.abs(y - handle.y) <= handleSize) {
      return handle.name
    }
  }
  
  return null
}

// 鼠标按下
const handleMouseDown = (e) => {
  if (e.button !== 0) return // 只处理左键
  
  const pos = getRelativePosition(e)
  dragState.startX = pos.x
  dragState.startY = pos.y
  dragState.currentX = pos.x
  dragState.currentY = pos.y
  
  // 检查是否点击在已有标注的调整手柄上
  if (selectedIssueId.value) {
    const handle = findResizeHandle(pos.x, pos.y, selectedIssue.value)
    if (handle) {
      dragState.isDragging = true
      dragState.mode = 'resize'
      dragState.resizeHandle = handle
      dragState.originalBbox = { ...selectedIssue.value.bbox }
      return
    }
  }
  
  // 检查是否点击在某个标注框内
  const clickedIssue = findIssueAtPosition(pos.x, pos.y)
  
  if (clickedIssue) {
    selectedIssueId.value = clickedIssue.id
    dragState.isDragging = true
    dragState.mode = 'move'
    dragState.originalBbox = { ...clickedIssue.bbox }
  } else {
    // 创建新标注
    selectedIssueId.value = null
    dragState.isDragging = true
    dragState.mode = 'create'
    newBox.x = pos.x
    newBox.y = pos.y
    newBox.width = 0
    newBox.height = 0
  }
}

// 鼠标移动
const handleMouseMove = (e) => {
  if (!dragState.isDragging) return
  
  const pos = getRelativePosition(e)
  dragState.currentX = pos.x
  dragState.currentY = pos.y
  
  if (dragState.mode === 'create') {
    // 创建新标注框
    newBox.width = Math.abs(pos.x - dragState.startX)
    newBox.height = Math.abs(pos.y - dragState.startY)
    newBox.x = Math.min(pos.x, dragState.startX)
    newBox.y = Math.min(pos.y, dragState.startY)
  } else if (dragState.mode === 'move' && selectedIssue.value) {
    // 移动标注框
    const deltaX = pos.x - dragState.startX
    const deltaY = pos.y - dragState.startY
    
    let newX = dragState.originalBbox.x + deltaX
    let newY = dragState.originalBbox.y + deltaY
    
    // 边界检查
    newX = Math.max(0, Math.min(100 - selectedIssue.value.bbox.width, newX))
    newY = Math.max(0, Math.min(100 - selectedIssue.value.bbox.height, newY))
    
    selectedIssue.value.bbox.x = newX
    selectedIssue.value.bbox.y = newY
  } else if (dragState.mode === 'resize' && selectedIssue.value) {
    // 调整大小
    const bbox = selectedIssue.value.bbox
    const original = dragState.originalBbox
    const deltaX = pos.x - dragState.startX
    const deltaY = pos.y - dragState.startY
    
    switch (dragState.resizeHandle) {
      case 'nw':
        bbox.x = Math.min(original.x + deltaX, original.x + original.width - 5)
        bbox.y = Math.min(original.y + deltaY, original.y + original.height - 5)
        bbox.width = original.width - (bbox.x - original.x)
        bbox.height = original.height - (bbox.y - original.y)
        break
      case 'ne':
        bbox.y = Math.min(original.y + deltaY, original.y + original.height - 5)
        bbox.width = Math.max(5, original.width + deltaX)
        bbox.height = original.height - (bbox.y - original.y)
        break
      case 'sw':
        bbox.x = Math.min(original.x + deltaX, original.x + original.width - 5)
        bbox.width = original.width - (bbox.x - original.x)
        bbox.height = Math.max(5, original.height + deltaY)
        break
      case 'se':
        bbox.width = Math.max(5, original.width + deltaX)
        bbox.height = Math.max(5, original.height + deltaY)
        break
    }
    
    // 边界检查
    bbox.x = Math.max(0, bbox.x)
    bbox.y = Math.max(0, bbox.y)
    if (bbox.x + bbox.width > 100) bbox.width = 100 - bbox.x
    if (bbox.y + bbox.height > 100) bbox.height = 100 - bbox.y
  }
}

// 鼠标释放
const handleMouseUp = () => {
  if (!dragState.isDragging) return
  
  if (dragState.mode === 'create' && newBox.width > 2 && newBox.height > 2) {
    // 创建新标注
    const newIssue = {
      id: `issue-new-${Date.now()}`,
      type: 'other',
      name: '其他',
      severity: 'warning',
      description: '请描述问题',
      confidence: 1.0,
      bbox: {
        x: newBox.x,
        y: newBox.y,
        width: newBox.width,
        height: newBox.height
      }
    }
    localIssues.value.push(newIssue)
    selectedIssueId.value = newIssue.id
    editingIssue.value = { ...newIssue }
  }
  
  // 重置拖拽状态
  dragState.isDragging = false
  dragState.mode = null
  dragState.resizeHandle = null
  dragState.originalBbox = null
  newBox.x = 0
  newBox.y = 0
  newBox.width = 0
  newBox.height = 0
}

// 选择标注
const selectIssue = (issue) => {
  selectedIssueId.value = issue.id
}

// 编辑问题详情
const openEditDialog = (issue) => {
  editingIssue.value = { ...issue }
}

// 保存问题编辑
const saveIssueEdit = () => {
  if (!editingIssue.value) return
  
  const index = localIssues.value.findIndex(i => i.id === editingIssue.value.id)
  if (index >= 0) {
    // 根据类型更新名称和严重程度
    const typeInfo = issueTypes.find(t => t.type === editingIssue.value.type)
    if (typeInfo) {
      editingIssue.value.name = typeInfo.name
      editingIssue.value.severity = typeInfo.severity
    }
    localIssues.value[index] = { ...editingIssue.value }
  }
  editingIssue.value = null
}

// 取消编辑
const cancelIssueEdit = () => {
  editingIssue.value = null
}

// 删除标注
const deleteIssue = (issueId) => {
  const index = localIssues.value.findIndex(i => i.id === issueId)
  if (index >= 0) {
    localIssues.value.splice(index, 1)
    if (selectedIssueId.value === issueId) {
      selectedIssueId.value = null
    }
  }
}

// 保存所有修改
const saveAll = () => {
  emit('save', localIssues.value)
}

// 取消
const cancel = () => {
  emit('cancel')
}

// 获取边框颜色
const getBorderColor = (severity) => {
  switch (severity) {
    case 'danger': return '#EF4444'
    case 'warning': return '#F97316'
    case 'caution': return '#EAB308'
    default: return '#6FBCCE'
  }
}

const getStatusBg = (severity) => {
  switch (severity) {
    case 'danger': return 'bg-accent-danger/20'
    case 'warning': return 'bg-accent-warning/20'
    case 'caution': return 'bg-accent-caution/20'
    default: return 'bg-brand-cyan/20'
  }
}
</script>

<template>
  <div class="flex gap-6">
    <!-- 左侧：图片和标注 -->
    <div class="flex-1">
      <div 
        ref="containerRef"
        class="relative select-none cursor-crosshair rounded-xl overflow-hidden"
        @mousedown="handleMouseDown"
        @mousemove="handleMouseMove"
        @mouseup="handleMouseUp"
        @mouseleave="handleMouseUp"
      >
        <!-- 图片 -->
        <img 
          ref="imageRef"
          :src="imageSrc"
          class="w-full block"
          @load="updateImageSize"
          draggable="false"
        >
        
        <!-- 已有标注框 -->
        <div 
          v-for="issue in localIssues"
          :key="issue.id"
          class="absolute border-2 rounded transition-shadow"
          :class="{
            'ring-2 ring-white ring-offset-2 ring-offset-transparent': selectedIssueId === issue.id
          }"
          :style="{
            left: issue.bbox.x + '%',
            top: issue.bbox.y + '%',
            width: issue.bbox.width + '%',
            height: issue.bbox.height + '%',
            borderColor: getBorderColor(issue.severity)
          }"
          @click.stop="selectIssue(issue)"
        >
          <!-- 标签 -->
          <span 
            class="absolute -top-6 left-0 px-2 py-0.5 text-xs rounded text-white whitespace-nowrap"
            :style="{ backgroundColor: getBorderColor(issue.severity) }"
          >
            {{ issue.name }}
          </span>
          
          <!-- 调整手柄（选中时显示） -->
          <template v-if="selectedIssueId === issue.id">
            <div class="absolute -top-1.5 -left-1.5 w-3 h-3 bg-white rounded-full cursor-nw-resize border-2 border-brand-primary"></div>
            <div class="absolute -top-1.5 -right-1.5 w-3 h-3 bg-white rounded-full cursor-ne-resize border-2 border-brand-primary"></div>
            <div class="absolute -bottom-1.5 -left-1.5 w-3 h-3 bg-white rounded-full cursor-sw-resize border-2 border-brand-primary"></div>
            <div class="absolute -bottom-1.5 -right-1.5 w-3 h-3 bg-white rounded-full cursor-se-resize border-2 border-brand-primary"></div>
          </template>
        </div>
        
        <!-- 新建标注框（拖拽时显示） -->
        <div 
          v-if="dragState.mode === 'create' && newBox.width > 0"
          class="absolute border-2 border-dashed border-brand-primary bg-brand-primary/10 rounded pointer-events-none"
          :style="{
            left: newBox.x + '%',
            top: newBox.y + '%',
            width: newBox.width + '%',
            height: newBox.height + '%'
          }"
        ></div>
      </div>
      
      <!-- 操作提示 -->
      <div class="mt-4 text-sm text-white/50">
        <p>💡 在图片上拖拽创建新标注 · 点击选中标注 · 拖拽角落调整大小</p>
      </div>
    </div>
    
    <!-- 右侧：标注列表和编辑 -->
    <div class="w-80 space-y-4">
      <!-- 标注列表 -->
      <div class="glass-card p-4">
        <h4 class="text-white font-semibold mb-3 flex items-center justify-between">
          <span>标注列表</span>
          <span class="text-brand-sky text-sm">{{ localIssues.length }} 个</span>
        </h4>
        
        <div v-if="localIssues.length === 0" class="text-white/50 text-sm text-center py-4">
          暂无标注，在图片上拖拽创建
        </div>
        
        <div v-else class="space-y-2 max-h-60 overflow-auto">
          <div 
            v-for="issue in localIssues"
            :key="issue.id"
            @click="selectIssue(issue)"
            class="p-3 rounded-lg cursor-pointer transition-colors flex items-center justify-between"
            :class="[
              getStatusBg(issue.severity),
              selectedIssueId === issue.id ? 'ring-2 ring-white/50' : ''
            ]"
          >
            <div>
              <div class="font-medium text-white text-sm">{{ issue.name }}</div>
              <div class="text-xs text-white/60 truncate max-w-[180px]">{{ issue.description }}</div>
            </div>
            <div class="flex items-center gap-2">
              <button 
                @click.stop="openEditDialog(issue)"
                class="p-1 hover:bg-white/20 rounded"
                title="编辑"
              >
                <svg class="w-4 h-4 text-white/70" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                </svg>
              </button>
              <button 
                @click.stop="deleteIssue(issue.id)"
                class="p-1 hover:bg-white/20 rounded"
                title="删除"
              >
                <svg class="w-4 h-4 text-accent-danger" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 编辑表单（选中时显示） -->
      <div v-if="editingIssue" class="glass-card p-4">
        <h4 class="text-white font-semibold mb-3">编辑标注</h4>
        
        <div class="space-y-3">
          <div>
            <label class="block text-sm text-white/60 mb-1">问题类型</label>
            <select 
              v-model="editingIssue.type"
              class="input-field text-sm"
            >
              <option v-for="type in issueTypes" :key="type.type" :value="type.type">
                {{ type.name }}
              </option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm text-white/60 mb-1">问题描述</label>
            <textarea 
              v-model="editingIssue.description"
              class="input-field text-sm min-h-[80px] resize-none"
              placeholder="请描述问题..."
            ></textarea>
          </div>
          
          <div class="flex gap-2">
            <button @click="cancelIssueEdit" class="flex-1 btn-secondary text-sm !py-2">
              取消
            </button>
            <button @click="saveIssueEdit" class="flex-1 btn-primary text-sm !py-2">
              确定
            </button>
          </div>
        </div>
      </div>
      
      <!-- 操作按钮 -->
      <div class="flex gap-3">
        <button @click="cancel" class="flex-1 btn-secondary">
          取消
        </button>
        <button @click="saveAll" class="flex-1 btn-primary">
          保存修改
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 自定义光标 */
.cursor-nw-resize { cursor: nw-resize; }
.cursor-ne-resize { cursor: ne-resize; }
.cursor-sw-resize { cursor: sw-resize; }
.cursor-se-resize { cursor: se-resize; }
</style>

