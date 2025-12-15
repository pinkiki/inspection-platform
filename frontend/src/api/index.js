import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 可以在这里添加token等
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// API 方法
export default {
  // 上传相关
  upload: {
    // 上传图片
    uploadImages(files, onProgress) {
      const formData = new FormData()
      files.forEach(file => {
        formData.append('files', file)
      })
      
      return api.post('/upload/images', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: onProgress
      })
    },
    
    // 获取上传的图片列表
    getImages(projectId) {
      return api.get(`/upload/images/${projectId}`)
    }
  },
  
  // 场景分析相关
  analysis: {
    // 分析场景
    analyzeScene(projectId) {
      return api.post(`/analysis/scene/${projectId}`)
    },
    
    // 获取可用算法
    getAlgorithms(sceneType) {
      return api.get(`/analysis/algorithms/${sceneType}`)
    }
  },
  
  // 报告相关
  report: {
    // 获取报告模板列表
    getTemplates(sceneType) {
      return api.get(`/report/templates/${sceneType}`)
    },
    
    // 选择模板
    selectTemplate(projectId, templateId) {
      return api.post(`/report/select-template`, { projectId, templateId })
    },
    
    // 执行检测
    runDetection(projectId) {
      return api.post(`/report/detect/${projectId}`)
    },
    
    // 获取检测结果
    getDetectionResults(projectId) {
      return api.get(`/report/detection-results/${projectId}`)
    },
    
    // 更新单张图片的检测结果
    updateDetectionResult(projectId, imageId, result) {
      return api.put(`/report/detection-result/${projectId}/${imageId}`, result)
    }
  },
  
  // 进阶报告相关
  advanced: {
    // 生成正射影像
    generateOrtho(projectId) {
      return api.post(`/advanced/ortho/${projectId}`)
    },
    
    // 生成3D模型
    generate3D(projectId) {
      return api.post(`/advanced/3d/${projectId}`)
    },
    
    // 获取进阶报告状态
    getStatus(projectId) {
      return api.get(`/advanced/status/${projectId}`)
    }
  },
  
  // 导出相关
  export: {
    // 更新项目信息
    updateProjectInfo(projectId, info) {
      return api.put(`/export/project-info/${projectId}`, info)
    },
    
    // 生成报告
    generateReport(projectId, format) {
      return api.post(`/export/generate/${projectId}`, { format })
    },
    
    // 下载报告
    downloadReport(projectId, format) {
      return api.get(`/export/download/${projectId}/${format}`, {
        responseType: 'blob'
      })
    },
    
    // 生成并下载PDF报告
    generatePDF(reportData) {
      return api.post('/export/generate-pdf', reportData, {
        responseType: 'blob',
        timeout: 60000  // 60秒超时，PDF生成可能需要较长时间
      })
    }
  }
}

