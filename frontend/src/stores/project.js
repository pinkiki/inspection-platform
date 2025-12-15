import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// 积分定价配置
export const CREDIT_PRICES = {
  SCENE_ANALYSIS: 20,          // 场景分析确认
  SCENE_REANALYSIS: 20,        // 场景重新分析
  TEMPLATE_BASIC: 0,           // 基础检测报告
  TEMPLATE_ORTHO: 99,          // 正射影像报告
  TEMPLATE_3D: 199,            // 三维模型报告
  TEMPLATE_FULL: 299           // 完整专业报告
}

// 处理阶段定义
export const PROCESSING_STAGES = {
  IDLE: 'idle',
  AERIAL_TRIANGULATION: 'aerial_triangulation',  // 空三加密
  DENSE_MATCHING: 'dense_matching',              // 密集匹配
  DEM_GENERATION: 'dem_generation',              // DEM生成
  ORTHO_GENERATION: 'ortho_generation',          // 正射影像生成
  MODEL_3D_RECONSTRUCTION: '3d_reconstruction',   // 三维模型重建
  TEXTURE_MAPPING: 'texture_mapping',            // 纹理映射
  COMPLETED: 'completed'
}

// 处理阶段中文名称
export const STAGE_NAMES = {
  [PROCESSING_STAGES.AERIAL_TRIANGULATION]: '空三加密',
  [PROCESSING_STAGES.DENSE_MATCHING]: '密集匹配',
  [PROCESSING_STAGES.DEM_GENERATION]: 'DEM生成',
  [PROCESSING_STAGES.ORTHO_GENERATION]: '正射影像生成',
  [PROCESSING_STAGES.MODEL_3D_RECONSTRUCTION]: '三维模型重建',
  [PROCESSING_STAGES.TEXTURE_MAPPING]: '纹理映射'
}

// 预计处理时间（小时）
export const ESTIMATED_TIME = {
  ortho: { min: 2, max: 4 },
  '3d': { min: 4, max: 8 },
  full: { min: 6, max: 10 }
}

// 额外资料类型优惠配置
export const SUPPLEMENTARY_DISCOUNTS = {
  pos: { discount: 10, timeSaved: '10-15分钟', skipStages: [] },
  sfm: { discount: 30, timeSaved: '30-60分钟', skipStages: ['aerial_triangulation', 'dense_matching'] },
  ortho: { discount: 50, timeSaved: '跳过正射生成', skipStages: ['ortho_generation'] },
  model3d: { discount: 50, timeSaved: '跳过模型重建', skipStages: ['3d_reconstruction', 'texture_mapping'] }
}

// 数据来源软件配置
export const DATA_SOURCES = {
  dji_terra: { name: '大疆智图', icon: '🛸' },
  metashape: { name: 'Metashape', icon: '📐' },
  pix4d: { name: 'Pix4D', icon: '🗺️' },
  context_capture: { name: 'Context Capture', icon: '🏗️' },
  other: { name: '其他/自定义', icon: '📁' }
}

export const useProjectStore = defineStore('project', () => {
  // 上传的图片列表
  const uploadedImages = ref([])
  
  // 当前项目ID
  const projectId = ref(null)
  
  // 场景分析结果
  const analysisResult = ref(null)
  
  // 选择的报告模板
  const selectedTemplate = ref(null)
  
  // 识别结果列表
  const detectionResults = ref([])
  
  // 进阶报告数据
  const advancedData = ref(null)
  
  // 项目信息（用于导出）
  const projectInfo = ref({
    name: '',
    location: '',
    inspectionDate: '',
    inspector: '',
    company: '',
    logo: null
  })
  
  // 当前步骤
  const currentStep = ref(1)
  
  // 项目是否完成
  const isProjectCompleted = ref(false)
  
  // 数据加载状态标记（防止重复加载）
  const dataLoadedFlags = ref({
    analysis: false,
    detection: false,
    advanced: false
  })
  
  // ========== 积分系统相关 ==========

  // 用户积分余额
  const userCredits = ref(10000)

  // 初始化时检查并充值（开发阶段辅助）
  if (userCredits.value < 10000) {
    const needRecharge = 10000 - userCredits.value
    userCredits.value = 10000
    console.log(`已自动充值 ${needRecharge} 积分，当前余额：10000`)
  }

  // 积分消费历史
  const creditsHistory = ref([])

  // ========== 个人信息相关 ==========

  // 当前用户信息
  const currentUser = ref({
    name: '张三',
    email: 'zhangsan@example.com',
    avatar: null,
    joinDate: '2024-01-15'
  })

  // 用户统计信息
  const userStats = ref({
    totalProjects: 12,
    totalReports: 8,
    lastLogin: new Date().toLocaleString()
  })

  // 步骤快照列表（最多保存10个）
  const stepSnapshots = ref([])

  // 个人信息模态框显示状态
  const showProfileModal = ref(false)
  
  // 进阶报告是否已处理完成
  const isAdvancedProcessed = ref(false)
  
  // 已支付的模板积分（用于计算升级差价）
  const paidTemplateCredits = ref(0)
  
  // ========== 进阶处理相关 ==========
  
  // 当前处理阶段
  const advancedProcessingStage = ref(PROCESSING_STAGES.IDLE)
  
  // 各阶段进度（0-100）
  const advancedProcessingProgress = ref({
    [PROCESSING_STAGES.AERIAL_TRIANGULATION]: 0,
    [PROCESSING_STAGES.DENSE_MATCHING]: 0,
    [PROCESSING_STAGES.DEM_GENERATION]: 0,
    [PROCESSING_STAGES.ORTHO_GENERATION]: 0,
    [PROCESSING_STAGES.MODEL_3D_RECONSTRUCTION]: 0,
    [PROCESSING_STAGES.TEXTURE_MAPPING]: 0
  })
  
  // 异步任务ID
  const advancedTaskId = ref(null)
  
  // 预计完成时间（ISO格式字符串）
  const advancedEstimatedTime = ref(null)
  
  // ========== 额外资料上传相关 ==========
  
  // 已上传的额外资料列表
  // 格式: { id, type, name, size, status, progress, file }
  const supplementaryFiles = ref([])
  
  // 选择的数据来源软件
  const selectedDataSource = ref(null)
  
  // 是否正在上传额外资料
  const isUploadingSupplementary = ref(false)
  
  // 额外资料带来的积分折扣
  const supplementaryDiscount = ref(0)
  
  // 是否需要进阶报告
  const needAdvancedReport = computed(() => {
    return selectedTemplate.value?.includeOrtho || selectedTemplate.value?.include3D
  })
  
  // 项目是否有未保存的数据
  const hasUnsavedData = computed(() => {
    return projectId.value && !isProjectCompleted.value && currentStep.value > 1
  })
  
  // 统计数据
  const statistics = computed(() => {
    const total = detectionResults.value.length
    const withIssues = detectionResults.value.filter(r => r.issues?.length > 0).length
    const avgConfidence = detectionResults.value.length > 0
      ? (detectionResults.value.reduce((sum, r) => sum + (r.confidence || 0), 0) / total).toFixed(2)
      : 0
    
    return {
      totalImages: total,
      imagesWithIssues: withIssues,
      issueCount: detectionResults.value.reduce((sum, r) => sum + (r.issues?.length || 0), 0),
      avgConfidence
    }
  })
  
  // 积分余额是否充足
  const hasLowCredits = computed(() => {
    return userCredits.value < 100
  })
  
  // 根据已上传的额外资料计算可跳过的处理阶段
  const skippedStages = computed(() => {
    const skipped = new Set()
    supplementaryFiles.value
      .filter(f => f.status === 'completed')
      .forEach(file => {
        const config = SUPPLEMENTARY_DISCOUNTS[file.type]
        if (config?.skipStages) {
          config.skipStages.forEach(stage => skipped.add(stage))
        }
      })
    return Array.from(skipped)
  })
  
  // 是否有已上传的额外资料
  const hasSupplementaryData = computed(() => {
    return supplementaryFiles.value.some(f => f.status === 'completed')
  })
  
  // 获取模板所需积分
  const getTemplateCredits = (templateId) => {
    const creditsMap = {
      'basic': CREDIT_PRICES.TEMPLATE_BASIC,
      'ortho': CREDIT_PRICES.TEMPLATE_ORTHO,
      '3d': CREDIT_PRICES.TEMPLATE_3D,
      'full': CREDIT_PRICES.TEMPLATE_FULL
    }
    return creditsMap[templateId] || 0
  }
  
  // 计算模板升级差价
  const getTemplateUpgradeCost = (fromTemplateId, toTemplateId) => {
    const fromCredits = getTemplateCredits(fromTemplateId)
    const toCredits = getTemplateCredits(toTemplateId)
    return Math.max(0, toCredits - fromCredits)
  }
  
  // Actions
  function setUploadedImages(images) {
    uploadedImages.value = images
  }
  
  function setProjectId(id) {
    projectId.value = id
  }
  
  function setAnalysisResult(result) {
    analysisResult.value = result
    dataLoadedFlags.value.analysis = true
  }
  
  function setSelectedTemplate(template) {
    selectedTemplate.value = template
  }
  
  function setDetectionResults(results) {
    detectionResults.value = results
    dataLoadedFlags.value.detection = true
  }
  
  function updateDetectionResult(index, result) {
    if (index >= 0 && index < detectionResults.value.length) {
      detectionResults.value[index] = { ...detectionResults.value[index], ...result }
    }
  }
  
  // 通过图片ID更新检测结果
  function updateDetectionResultById(imageId, updates) {
    const index = detectionResults.value.findIndex(r => r.id === imageId || r.image_id === imageId)
    if (index >= 0) {
      detectionResults.value[index] = { ...detectionResults.value[index], ...updates }
    }
  }
  
  function setAdvancedData(data) {
    advancedData.value = data
    dataLoadedFlags.value.advanced = true
  }
  
  function setProjectInfo(info) {
    projectInfo.value = { ...projectInfo.value, ...info }
  }
  
  function setCurrentStep(step) {
    currentStep.value = step
  }
  
  function setProjectCompleted(completed) {
    isProjectCompleted.value = completed
  }
  
  // 检查数据是否已加载
  function isDataLoaded(key) {
    return dataLoadedFlags.value[key] === true
  }
  
  // 重置数据加载状态
  function resetDataLoadedFlag(key) {
    if (key) {
      dataLoadedFlags.value[key] = false
    } else {
      dataLoadedFlags.value = {
        analysis: false,
        detection: false,
        advanced: false
      }
    }
  }
  
  // ========== 积分管理方法 ==========
  
  // 检查积分是否足够
  function canAfford(amount) {
    // 管理员模式下积分无限
    if (localStorage.getItem('adminMode') === 'true') {
      return true
    }
    return userCredits.value >= amount
  }
  
  // 扣除积分
  async function deductCredits(amount, reason) {
    if (!canAfford(amount)) {
      return false
    }

    const isAdmin = localStorage.getItem('adminMode') === 'true'
    const balanceBefore = userCredits.value

    // 管理员模式下不实际扣除积分
    if (!isAdmin) {
      userCredits.value -= amount
    }

    const balanceAfter = userCredits.value

    // 调用后端API记录积分变化
    try {
      await fetch('/api/credits/deduct', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: 1,
          amount: amount,
          reason: reason + (isAdmin ? ' [管理员模式]' : ''),
          balance_before: balanceBefore,
          balance_after: balanceAfter
        })
      })
    } catch (error) {
      console.error('记录积分扣除失败:', error)
    }

    // 记录消费历史（本地）
    creditsHistory.value.unshift({
      id: Date.now(),
      amount: -amount,
      reason: reason + (isAdmin ? ' [管理员模式]' : ''),
      balance: userCredits.value,
      timestamp: new Date().toISOString()
    })

    // 限制历史记录数量
    if (creditsHistory.value.length > 50) {
      creditsHistory.value = creditsHistory.value.slice(0, 50)
    }

    return true
  }

  // 增加积分（充值或退款）
  async function addCredits(amount, reason) {
    const balanceBefore = userCredits.value
    userCredits.value += amount
    const balanceAfter = userCredits.value

    // 调用后端API记录积分变化
    try {
      await fetch('/api/credits/add', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: 1,
          amount: amount,
          reason: reason,
          balance_before: balanceBefore,
          balance_after: balanceAfter
        })
      })
    } catch (error) {
      console.error('记录积分增加失败:', error)
    }

    creditsHistory.value.unshift({
      id: Date.now(),
      amount: amount,
      reason: reason,
      balance: userCredits.value,
      timestamp: new Date().toISOString()
    })

    if (creditsHistory.value.length > 50) {
      creditsHistory.value = creditsHistory.value.slice(0, 50)
    }
  }
  
  // 设置进阶处理完成状态
  function setAdvancedProcessed(processed) {
    isAdvancedProcessed.value = processed
  }
  
  // 设置已支付的模板积分
  function setPaidTemplateCredits(credits) {
    paidTemplateCredits.value = credits
  }
  
  // ========== 进阶处理管理方法 ==========
  
  // 设置处理阶段
  function setProcessingStage(stage) {
    advancedProcessingStage.value = stage
  }
  
  // 设置阶段进度
  function setStageProgress(stage, progress) {
    advancedProcessingProgress.value[stage] = progress
  }
  
  // 重置所有进度
  function resetProcessingProgress() {
    advancedProcessingStage.value = PROCESSING_STAGES.IDLE
    Object.keys(advancedProcessingProgress.value).forEach(key => {
      advancedProcessingProgress.value[key] = 0
    })
    advancedTaskId.value = null
    advancedEstimatedTime.value = null
  }
  
  // 设置任务ID
  function setTaskId(taskId) {
    advancedTaskId.value = taskId
  }
  
  // 设置预计完成时间
  function setEstimatedTime(time) {
    advancedEstimatedTime.value = time
  }
  
  // 获取当前阶段进度
  function getCurrentStageProgress() {
    if (advancedProcessingStage.value === PROCESSING_STAGES.IDLE || 
        advancedProcessingStage.value === PROCESSING_STAGES.COMPLETED) {
      return 100
    }
    return advancedProcessingProgress.value[advancedProcessingStage.value] || 0
  }
  
  // ========== 额外资料上传管理方法 ==========
  
  // 设置数据来源
  function setDataSource(source) {
    selectedDataSource.value = source
  }
  
  // 添加额外资料文件到上传队列
  function addSupplementaryFiles(files, dataSource) {
    selectedDataSource.value = dataSource
    
    files.forEach(fileData => {
      const fileId = `sup-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      supplementaryFiles.value.push({
        id: fileId,
        type: fileData.type,
        name: fileData.name,
        size: fileData.size,
        file: fileData.file,
        status: 'pending', // pending, uploading, completed, error
        progress: 0
      })
    })
  }
  
  // 开始上传额外资料（模拟）
  function startSupplementaryUpload() {
    isUploadingSupplementary.value = true
    
    // 模拟逐个上传
    const pendingFiles = supplementaryFiles.value.filter(f => f.status === 'pending')
    
    pendingFiles.forEach((file, index) => {
      setTimeout(() => {
        uploadSingleFile(file.id)
      }, index * 500) // 错开开始时间
    })
  }
  
  // 上传单个文件（模拟）
  function uploadSingleFile(fileId) {
    const file = supplementaryFiles.value.find(f => f.id === fileId)
    if (!file) return
    
    file.status = 'uploading'
    file.progress = 0
    
    // 模拟上传进度
    const interval = setInterval(() => {
      if (file.progress >= 100) {
        clearInterval(interval)
        file.status = 'completed'
        
        // 检查是否所有文件都上传完成
        const allCompleted = supplementaryFiles.value.every(
          f => f.status === 'completed' || f.status === 'error'
        )
        if (allCompleted) {
          isUploadingSupplementary.value = false
          calculateSupplementaryDiscount()
        }
      } else {
        // 根据文件大小模拟不同的上传速度
        const increment = file.size > 100 * 1024 * 1024 
          ? Math.random() * 3 + 1  // 大文件慢一点
          : Math.random() * 8 + 4  // 小文件快一点
        file.progress = Math.min(100, file.progress + increment)
      }
    }, 200)
  }
  
  // 计算额外资料带来的折扣
  function calculateSupplementaryDiscount() {
    let totalDiscount = 0
    
    supplementaryFiles.value
      .filter(f => f.status === 'completed')
      .forEach(file => {
        const config = SUPPLEMENTARY_DISCOUNTS[file.type]
        if (config) {
          totalDiscount += config.discount
        }
      })
    
    // 限制最大折扣为70%
    supplementaryDiscount.value = Math.min(totalDiscount, 70)
  }
  
  // 重试上传失败的文件
  function retrySupplementaryUpload(fileId) {
    const file = supplementaryFiles.value.find(f => f.id === fileId)
    if (file && file.status === 'error') {
      file.status = 'pending'
      file.progress = 0
      isUploadingSupplementary.value = true
      uploadSingleFile(fileId)
    }
  }
  
  // 取消上传
  function cancelSupplementaryUpload(fileId) {
    const index = supplementaryFiles.value.findIndex(f => f.id === fileId)
    if (index !== -1) {
      supplementaryFiles.value.splice(index, 1)
      
      // 检查是否还有正在上传的文件
      const hasUploading = supplementaryFiles.value.some(f => f.status === 'uploading')
      if (!hasUploading) {
        isUploadingSupplementary.value = false
      }
    }
  }
  
  // 清除已完成的上传记录
  function clearCompletedSupplementaryFiles() {
    // 只在没有正在上传的文件时清除
    if (!isUploadingSupplementary.value) {
      supplementaryFiles.value = []
      selectedDataSource.value = null
    }
  }
  
  // 重置额外资料状态
  function resetSupplementaryData() {
    supplementaryFiles.value = []
    selectedDataSource.value = null
    isUploadingSupplementary.value = false
    supplementaryDiscount.value = 0
  }
  
  // 获取已上传资料的类型列表
  function getUploadedSupplementaryTypes() {
    return supplementaryFiles.value
      .filter(f => f.status === 'completed')
      .map(f => f.type)
  }

  // ========== 个人信息相关方法 ==========

  // 创建步骤快照
  function createSnapshot() {
    const snapshot = {
      id: Date.now(),
      step: currentStep.value,
      stepName: getStepName(currentStep.value),
      timestamp: new Date().toISOString(),
      imageCount: uploadedImages.value.length,
      templateName: selectedTemplate.value?.name || '未选择',
      analysisResult: analysisResult.value ? { ...analysisResult.value } : null,
      selectedTemplate: selectedTemplate.value ? { ...selectedTemplate.value } : null,
      detectionResults: [...detectionResults.value],
      projectInfo: { ...projectInfo.value },
      userCredits: userCredits.value,
      creditsHistory: [...creditsHistory.value]
    }

    // 添加到快照列表，最多保留10个
    stepSnapshots.value.unshift(snapshot)
    if (stepSnapshots.value.length > 10) {
      stepSnapshots.value = stepSnapshots.value.slice(0, 10)
    }

    return snapshot
  }

  // 恢复步骤快照
  function restoreSnapshot(snapshotId) {
    const snapshot = stepSnapshots.value.find(s => s.id === snapshotId)
    if (!snapshot) {
      console.error('快照不存在')
      return false
    }

    try {
      // 恢复所有状态
      currentStep.value = snapshot.step
      uploadedImages.value = [] // 需要重新上传图片
      analysisResult.value = snapshot.analysisResult
      selectedTemplate.value = snapshot.selectedTemplate
      detectionResults.value = snapshot.detectionResults
      projectInfo.value = snapshot.projectInfo
      userCredits.value = snapshot.userCredits
      creditsHistory.value = snapshot.creditsHistory

      // 从快照列表中移除已恢复的快照
      stepSnapshots.value = stepSnapshots.value.filter(s => s.id !== snapshotId)

      return true
    } catch (error) {
      console.error('恢复快照失败:', error)
      return false
    }
  }

  // 获取步骤名称
  function getStepName(stepId) {
    const stepNames = {
      1: '图像上传',
      2: '场景分析',
      3: '报告模板',
      4: '识别审查',
      5: '进阶报告',
      6: '报告导出'
    }
    return stepNames[stepId] || `步骤${stepId}`
  }

  // 获取用户等级
  function getUserLevel() {
    const totalCredits = creditsHistory.value
      .filter(record => record.type === 'earn')
      .reduce((sum, record) => sum + record.amount, 0)

    if (totalCredits >= 5000) return 'VIP 5'
    if (totalCredits >= 3000) return 'VIP 4'
    if (totalCredits >= 2000) return 'VIP 3'
    if (totalCredits >= 1000) return 'VIP 2'
    if (totalCredits >= 500) return 'VIP 1'
    return '普通用户'
  }

  // 获取下一等级信息
  function getNextLevel() {
    const currentLevel = getUserLevel()
    const totalCredits = creditsHistory.value
      .filter(record => record.type === 'earn')
      .reduce((sum, record) => sum + record.amount, 0)

    const levels = [
      { name: '普通用户', required: 0, next: 'VIP 1' },
      { name: 'VIP 1', required: 500, next: 'VIP 2' },
      { name: 'VIP 2', required: 1000, next: 'VIP 3' },
      { name: 'VIP 3', required: 2000, next: 'VIP 4' },
      { name: 'VIP 4', required: 3000, next: 'VIP 5' },
      { name: 'VIP 5', required: 5000, next: null }
    ]

    const currentLevelInfo = levels.find(l => l.name === currentLevel)
    if (!currentLevelInfo || !currentLevelInfo.next) {
      return null
    }

    const nextLevelInfo = levels.find(l => l.name === currentLevelInfo.next)
    const creditsNeeded = nextLevelInfo.required - totalCredits
    const creditsFromLastLevel = totalCredits - currentLevelInfo.required
    const creditsPerLevel = nextLevelInfo.required - currentLevelInfo.required
    const progress = Math.min(100, Math.max(0, (creditsFromLastLevel / creditsPerLevel) * 100))

    return {
      level: nextLevelInfo.name,
      creditsNeeded: Math.max(0, creditsNeeded),
      progress: progress
    }
  }

  // 自动保存步骤快照
  function autoSaveSnapshot() {
    if (currentStep.value > 1) { // 从第2步开始自动保存
      createSnapshot()
    }
  }
  
  // 验证模板切换是否允许
  function canSwitchTemplate(targetTemplateId) {
    if (!selectedTemplate.value) {
      return { allowed: true, reason: '' }
    }
    
    // 如果还未进行进阶处理，可以自由切换
    if (!isAdvancedProcessed.value) {
      return { allowed: true, reason: '' }
    }
    
    // 已完成进阶处理，只能升级不能降级
    const templateLevel = {
      'basic': 0,
      'ortho': 1,
      '3d': 2,
      'full': 3
    }
    
    const currentLevel = templateLevel[selectedTemplate.value.id] || 0
    const targetLevel = templateLevel[targetTemplateId] || 0
    
    if (targetLevel >= currentLevel) {
      return { allowed: true, reason: '升级' }
    }
    
    return {
      allowed: false,
      reason: '已生成进阶报告，无法切换到低级模板'
    }
  }
  
  function resetProject() {
    uploadedImages.value = []
    projectId.value = null
    analysisResult.value = null
    selectedTemplate.value = null
    detectionResults.value = []
    advancedData.value = null
    projectInfo.value = {
      name: '',
      location: '',
      inspectionDate: '',
      inspector: '',
      company: '',
      logo: null
    }
    currentStep.value = 1
    isProjectCompleted.value = false
    dataLoadedFlags.value = {
      analysis: false,
      detection: false,
      advanced: false
    }
    // 重置进阶处理状态
    isAdvancedProcessed.value = false
    paidTemplateCredits.value = 0
    // 重置额外资料状态
    resetSupplementaryData()
    // 注意：不重置积分和积分历史
  }
  
  return {
    // State
    uploadedImages,
    projectId,
    analysisResult,
    selectedTemplate,
    detectionResults,
    advancedData,
    projectInfo,
    currentStep,
    isProjectCompleted,
    dataLoadedFlags,
    // 积分相关状态
    userCredits,
    creditsHistory,
    isAdvancedProcessed,
    paidTemplateCredits,
    // 进阶处理相关状态
    advancedProcessingStage,
    advancedProcessingProgress,
    advancedTaskId,
    advancedEstimatedTime,
    // 额外资料上传相关状态
    supplementaryFiles,
    selectedDataSource,
    isUploadingSupplementary,
    supplementaryDiscount,
    // Computed
    needAdvancedReport,
    hasUnsavedData,
    statistics,
    hasLowCredits,
    skippedStages,
    hasSupplementaryData,
    // Actions
    setUploadedImages,
    setProjectId,
    setAnalysisResult,
    setSelectedTemplate,
    setDetectionResults,
    updateDetectionResult,
    updateDetectionResultById,
    setAdvancedData,
    setProjectInfo,
    setCurrentStep,
    setProjectCompleted,
    isDataLoaded,
    resetDataLoadedFlag,
    resetProject,
    // 积分相关方法
    canAfford,
    deductCredits,
    addCredits,
    setAdvancedProcessed,
    setPaidTemplateCredits,
    canSwitchTemplate,
    getTemplateCredits,
    getTemplateUpgradeCost,
    // 进阶处理相关方法
    setProcessingStage,
    setStageProgress,
    resetProcessingProgress,
    setTaskId,
    setEstimatedTime,
    getCurrentStageProgress,
    // 额外资料上传相关方法
    setDataSource,
    addSupplementaryFiles,
    startSupplementaryUpload,
    retrySupplementaryUpload,
    cancelSupplementaryUpload,
    clearCompletedSupplementaryFiles,
    resetSupplementaryData,
    getUploadedSupplementaryTypes,
    // 个人信息相关方法
    createSnapshot,
    restoreSnapshot,
    getStepName,
    getUserLevel,
    getNextLevel,
    autoSaveSnapshot
  }
}, {
  // 持久化配置
  persist: {
    key: 'inspection-project',
    storage: localStorage,
    paths: [
      'uploadedImages',
      'projectId',
      'analysisResult',
      'selectedTemplate',
      'detectionResults',
      'advancedData',
      'projectInfo',
      'currentStep',
      'isProjectCompleted',
      'dataLoadedFlags',
      // 积分相关
      'userCredits',
      'creditsHistory',
      'isAdvancedProcessed',
      'paidTemplateCredits',
      // 进阶处理相关
      'advancedProcessingStage',
      'advancedProcessingProgress',
      'advancedTaskId',
      'advancedEstimatedTime',
      // 额外资料上传相关
      'supplementaryFiles',
      'selectedDataSource',
      'supplementaryDiscount',
      // 个人信息相关
      'currentUser',
      'userStats',
      'stepSnapshots',
      'showProfileModal'
    ]
  }
})
