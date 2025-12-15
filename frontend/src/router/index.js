import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'upload',
    component: () => import('../views/UploadView.vue'),
    meta: { step: 1, title: '图像上传' }
  },
  {
    path: '/analysis',
    name: 'analysis',
    component: () => import('../views/AnalysisView.vue'),
    meta: { step: 2, title: '场景分析' }
  },
  {
    path: '/template',
    name: 'template',
    component: () => import('../views/TemplateView.vue'),
    meta: { step: 3, title: '报告模板' }
  },
  {
    path: '/review',
    name: 'review',
    component: () => import('../views/ReviewView.vue'),
    meta: { step: 4, title: '识别审查' }
  },
  {
    path: '/advanced',
    name: 'advanced',
    component: () => import('../views/AdvancedView.vue'),
    meta: { step: 5, title: '进阶报告' }
  },
  {
    path: '/export',
    name: 'export',
    component: () => import('../views/ExportView.vue'),
    meta: { step: 6, title: '报告导出' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

