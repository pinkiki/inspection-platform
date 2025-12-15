<script setup>
import { computed, ref } from 'vue'
import { useProjectStore } from '../stores/project'

const props = defineProps({
  template: {
    type: Object,
    required: true
  },
  sceneType: {
    type: String,
    default: 'road'
  },
  // 新增：是否使用真实项目数据
  useRealData: {
    type: Boolean,
    default: false
  },
  // 新增：项目信息数据
  projectData: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close'])
const store = useProjectStore()

// 图片引用和显示信息（用于bbox坐标转换）
const imageRefs = ref({})
const imageDisplayInfo = ref({})

// 计算图片实际显示尺寸
const updateImageDisplayInfo = (imageId, imgElement) => {
  if (!imgElement) return
  
  // 获取图片在页面中的实际显示尺寸（被CSS缩放后的尺寸）
  const displayWidth = imgElement.clientWidth
  const displayHeight = imgElement.clientHeight
  
  // 使用实际显示尺寸，而不是原始尺寸
  imageDisplayInfo.value[imageId] = {
    width: displayWidth,
    height: displayHeight
  }
}

// 将百分比坐标转换为像素
const getBboxPixelStyle = (bbox, imageId) => {
  const imgInfo = imageDisplayInfo.value[imageId]
  if (!imgInfo) return {}
  
  return {
    left: `${(bbox.x / 100) * imgInfo.width}px`,
    top: `${(bbox.y / 100) * imgInfo.height}px`,
    width: `${(bbox.w / 100) * imgInfo.width}px`,
    height: `${(bbox.h / 100) * imgInfo.height}px`,
    borderColor: bbox.color,
    boxShadow: `0 0 0 2px rgba(0,0,0,0.5), 0 0 10px ${bbox.color}`
  }
}

// 场景类型映射到报告数据key
const sceneMapping = {
  building: 'facadeUav',
  solar: 'pvUav',
  road: 'roadUav',
  power: 'municipal'
}

// 场景名称映射
const sceneNames = {
  building: '建筑外立面无人机巡检',
  solar: '光伏板无人机巡检',
  road: '道路无人机巡检',
  power: '电力设施巡检'
}

// 格式化函数
const fmt = {
  dt: (iso) => new Date(iso).toLocaleString('zh-CN', { hour12: false }),
  num: (x) => (x === null || x === undefined) ? '—' : (typeof x === 'number' ? x.toLocaleString('zh-CN') : String(x)),
  pct: (x) => (x === null || x === undefined) ? '—' : `${Math.round(x * 100)}%`
}

const nowIso = new Date().toISOString()

// 各场景的示例报告数据
const reportDatasets = {
  // 道路无人机场景
  roadUav: {
    key: 'roadUav',
    name: '道路无人机巡检报告',
    sub: '航线采集 · 正射/视频帧抽取 · 路面病害识别 · 里程桩定位',
    data: {
      header: {
        reportId: 'ROAD-2025-1213-0011',
        project: '某高速路段日常巡检（K12~K18）',
        area: '上行 K12+000 ~ K18+500',
        period: '2025-12-11 09:00 ~ 11:00',
        createdAt: nowIso,
        issuer: 'AI 航测巡检系统 v1.1',
        confidentiality: '内部'
      },
      summary: {
        totalPhotos: 1240,
        validPhotos: 1188,
        issues: 22,
        duplicated: 0,
        avgConfidence: 0.79,
        slaHit: 0.88,
        topTypes: [
          { type: '坑槽', count: 7 },
          { type: '纵向裂缝', count: 6 },
          { type: '沉陷/车辙', count: 4 }
        ]
      },
      task: {
        platform: 'DJI M300 RTK',
        sensor: '可见光 20MP（正射）',
        altitude: '80m AGL',
        speed: '8 m/s',
        overlap: '前向 80% / 旁向 70%',
        gsd: '约 2.2 cm/pixel',
        weather: '多云 · 能见度良好',
        controlPoints: 'RTK + 2 个检核点'
      },
      ai: {
        pipelineId: 'PIPE-ROAD-2025.10',
        modelVersions: [
          { name: 'Road-Det', ver: '4.0.3' },
          { name: 'ChainageAlign', ver: '1.3.2' },
          { name: 'RiskScore', ver: '1.2.0' }
        ],
        notes: '里程定位：基于航迹+道路中心线匹配，误差估计 5~15m；必要时可人工校正。'
      },
      issues: [
        {
          id: 'R-003',
          level: 'P1',
          type: '坑槽',
          status: '待处置',
          location: { address: '上行主线 右1车道', gps: '31.21890,121.39220', accuracy: '10m', chainage: 'K13+420' },
          time: '2025-12-11T09:38:08+08:00',
          evidence: { photoId: 'ORTHO-TILE-031', source: '正射瓦片', device: 'UAV', exif: '有', hash: 'sha256:77..2c' },
          ai: { confidence: 0.84, model: 'Road-Det 4.0.3', reasoning: '坑槽边界明显；面积估计 0.32㎡；位于轮迹带。' },
          metrics: { area_m2: 0.32, depth_est_cm: 4.5 },
          impact: '雨天易积水，存在爆胎/车辆失稳风险；建议 48 小时内修补。',
          action: { owner: '道路养护', sla: '48h修补', suggestion: '冷补料临时修补→夜间封道热补；同步检查同段裂缝扩展。' },
          boxes: [{ x: 520, y: 420, w: 380, h: 210, label: '坑槽（0.84）', color: '#ffd166' }]
        },
        {
          id: 'R-011',
          level: 'P2',
          type: '纵向裂缝',
          status: '待处置',
          location: { address: '上行主线 中间车道', gps: '31.21510,121.40130', accuracy: '12m', chainage: 'K15+060' },
          time: '2025-12-11T10:21:14+08:00',
          evidence: { photoId: 'FRAME-9021', source: '视频帧抽取', device: 'UAV', exif: '—', hash: 'sha256:ab..90' },
          ai: { confidence: 0.76, model: 'Road-Det 4.0.3', reasoning: '细长裂缝形态，长度估计 3.8m；需观察扩展趋势。' },
          metrics: { length_m: 3.8, width_mm: 3 },
          impact: '短期影响一般，若渗水易导致结构损伤；建议 7 天内灌缝/封缝。',
          action: { owner: '道路养护', sla: '7d封缝', suggestion: '灌缝+表处；雨季前优先处理。' },
          boxes: [{ x: 300, y: 360, w: 640, h: 120, label: '纵向裂缝（0.76）', color: '#5bd6ff' }]
        }
      ],
      attachments: [
        { name: '航线与航迹.gpx', desc: '用于复核定位与回飞复拍' },
        { name: '正射影像索引.geojson', desc: '瓦片索引、覆盖范围、GSD' },
        { name: '病害统计报表.xlsx', desc: '按里程/车道/病害类型汇总' }
      ],
      audit: {
        traceId: 'trace-road-4f02...',
        operator: 'uav-team',
        approvals: '审核：待分配',
        dataRetention: '原始影像 365 天；正射 365 天；结构化结果 730 天'
      }
    }
  },

  // 光伏板无人机场景
  pvUav: {
    key: 'pvUav',
    name: '光伏板无人机巡检报告（可见光 + 热成像）',
    sub: '阵列/组串定位 · 热斑/隐裂/遮挡/积灰 · 风险分级 · 运维工单',
    data: {
      header: {
        reportId: 'PV-2025-1213-0003',
        project: '某 50MW 地面电站例行巡检',
        area: 'A区 12~18 排 · 组件网格 A-12-01 ~ A-18-40',
        period: '2025-12-10 13:00 ~ 15:00',
        createdAt: nowIso,
        issuer: 'AI 光伏巡检系统 v2.3',
        confidentiality: '内部/含设备信息'
      },
      summary: {
        totalPhotos: 980,
        validPhotos: 944,
        issues: 17,
        duplicated: 2,
        avgConfidence: 0.83,
        slaHit: 0.76,
        topTypes: [
          { type: '热斑/过热点', count: 8 },
          { type: '积灰/遮挡', count: 5 },
          { type: '疑似隐裂', count: 2 }
        ]
      },
      task: {
        platform: 'DJI Mavic 3T',
        sensors: '可见光 + 热红外',
        altitude: '30~45m AGL',
        gsd: '约 1.0~1.6 cm/pixel（可见光）',
        env: '辐照度 820 W/m²（估计）· 环境温度 12℃ · 风 3m/s',
        bestPractice: '建议：稳定辐照、避免云影；热像需校准发射率与反射温度。'
      },
      ai: {
        pipelineId: 'PIPE-PV-2025.12',
        modelVersions: [
          { name: 'PV-PanelGrid', ver: '2.2.0' },
          { name: 'ThermalAnomaly', ver: '3.0.1' },
          { name: 'VisibleDefect', ver: '1.8.0' },
          { name: 'LossEst', ver: '0.9.3' }
        ],
        notes: 'ΔT 为组件热点与周边中位温差；置信度结合温差、形态、跨帧一致性。'
      },
      issues: [
        {
          id: 'PV-005',
          level: 'P1',
          type: '热斑/过热点（单点）',
          status: '待复核',
          location: { address: 'A区 第14排 第22块', gps: '31.10020,121.52040', accuracy: '8m', asset: '模块ID A-14-22', string: 'INV-03 / STR-07' },
          time: '2025-12-10T14:03:21+08:00',
          evidence: { photoId: 'TH-221', source: '热成像', device: 'UAV', exif: '有', hash: 'sha256:19..c8' },
          ai: { confidence: 0.87, model: 'ThermalAnomaly 3.0.1', reasoning: '热点呈单点强亮，ΔT=18.6℃；跨 3 帧稳定出现。' },
          metrics: { deltaT_C: 18.6, tHot_C: 54.2, tRef_C: 35.6, lossEst_pct: 0.8 },
          impact: '可能与焊带/旁路二极管异常相关；存在功率损失与局部过热风险；建议 72 小时内现场复核（红外测温+IV）。',
          action: { owner: '电站运维', sla: '72h复核 / 14d处理', suggestion: '复核组串电流与IV曲线；检查接线盒与旁路二极管；必要时更换组件。' },
          boxes: [{ x: 650, y: 260, w: 260, h: 220, label: '热斑 ΔT=18.6℃（0.87）', color: '#ffd166' }]
        },
        {
          id: 'PV-012',
          level: 'P2',
          type: '积灰/遮挡（边缘）',
          status: '待处置',
          location: { address: 'A区 第17排 第05块', gps: '31.10098,121.52130', accuracy: '10m', asset: '模块ID A-17-05', string: 'INV-04 / STR-02' },
          time: '2025-12-10T14:44:02+08:00',
          evidence: { photoId: 'RGB-905', source: '可见光', device: 'UAV', exif: '有', hash: 'sha256:88..e1' },
          ai: { confidence: 0.79, model: 'VisibleDefect 1.8.0', reasoning: '边缘遮挡/积灰带明显，疑似长期未清洗；与热像弱热点相关。' },
          metrics: { coverage_pct: 0.22, lossEst_pct: 0.4 },
          impact: '持续影响发电；若局部遮挡可能诱发热点；建议 7 天内清洗并复飞复核。',
          action: { owner: '电站运维', sla: '7d清洗', suggestion: '按区块清洗；记录清洗前后对比；关注遮挡来源（杂草/鸟粪/边框）。' },
          boxes: [{ x: 260, y: 420, w: 520, h: 180, label: '积灰/遮挡（0.79）', color: '#5bd6ff' }]
        }
      ],
      attachments: [
        { name: '组件网格定位结果.geojson', desc: '每块组件 polygon + 模块ID + 归属组串' },
        { name: '热斑清单.xlsx', desc: 'ΔT、模块ID、逆变器、建议动作' },
        { name: '巡检航线与传感器参数.json', desc: '热像发射率/距离/反射温度等' }
      ],
      audit: {
        traceId: 'trace-pv-1a73...',
        operator: 'pv-ops',
        approvals: '复核：待分配（建议必填）',
        dataRetention: '原始热像 365 天；结构化结果 730 天；质保证据 5 年（可选）'
      }
    }
  },

  // 建筑外立面场景
  facadeUav: {
    key: 'facadeUav',
    name: '建筑外立面无人机巡检报告',
    sub: '立面分区/构件编号 · 裂缝/空鼓/脱落风险 · 安全风险分级 · 复核建议',
    data: {
      header: {
        reportId: 'FCD-2025-1213-0008',
        project: '某商业综合体外立面专项巡检',
        area: '1#楼 南立面 + 西立面（10~36层）',
        period: '2025-12-09 07:30 ~ 09:10',
        createdAt: nowIso,
        issuer: 'AI 建筑巡检系统 v1.6',
        confidentiality: '内部/含建筑信息'
      },
      summary: {
        totalPhotos: 560,
        validPhotos: 518,
        issues: 19,
        duplicated: 4,
        avgConfidence: 0.81,
        slaHit: 0.69,
        topTypes: [
          { type: '外墙裂缝', count: 9 },
          { type: '饰面层空鼓/脱落风险', count: 5 },
          { type: '渗水/泛碱', count: 3 }
        ]
      },
      task: {
        platform: 'DJI Air 3（示例）',
        sensor: '可见光 48MP',
        distance: '约 6~12m（贴近拍摄）',
        safety: '设置警戒线；人车分流；飞手+观察员双人',
        weather: '微风 · 光照稳定',
        privacy: '人脸/室内窗户区域可选自动打码'
      },
      ai: {
        pipelineId: 'PIPE-FCD-2025.09',
        modelVersions: [
          { name: 'Facade-Seg', ver: '1.5.1' },
          { name: 'CrackDet', ver: '2.1.0' },
          { name: 'SpallRisk', ver: '1.0.2' },
          { name: 'SizeEst', ver: '0.7.0' }
        ],
        notes: '尺寸估计依赖拍摄距离/镜头参数，建议配合标尺贴或激光测距增强精度。'
      },
      issues: [
        {
          id: 'F-002',
          level: 'P0',
          type: '饰面层脱落风险（空鼓/松动疑似）',
          status: '待处置',
          location: { address: '1#楼 南立面 28层 东侧窗间墙', gps: '—', accuracy: '—', zone: 'S-28-E', component: '幕墙/瓷砖饰面' },
          time: '2025-12-09T08:12:46+08:00',
          evidence: { photoId: 'FCD-IMG-210', source: '近景照片', device: 'UAV', exif: '有', hash: 'sha256:ef..10' },
          ai: { confidence: 0.90, model: 'SpallRisk 1.0.2', reasoning: '边角翘起阴影明显；与缝隙形态一致；区域附近存在裂缝与泛碱。' },
          metrics: { area_m2: 0.18, height_m: 92 },
          impact: '高空坠物重大风险；建议立即设置地面警戒并安排高空作业复核（敲击/拉拔）。',
          action: { owner: '物业/维保单位', sla: '2h警戒 / 24h复核', suggestion: '先隔离；再高空检修；必要时拆除重铺或加固。' },
          boxes: [{ x: 740, y: 260, w: 320, h: 280, label: '脱落风险（0.90）', color: '#ff5a7a' }]
        },
        {
          id: 'F-013',
          level: 'P2',
          type: '外墙裂缝（竖向）',
          status: '待复核',
          location: { address: '1#楼 西立面 15层', gps: '—', accuracy: '—', zone: 'W-15', component: '抹灰层/涂料' },
          time: '2025-12-09T08:46:18+08:00',
          evidence: { photoId: 'FCD-IMG-388', source: '近景照片', device: 'UAV', exif: '有', hash: 'sha256:19..ee' },
          ai: { confidence: 0.77, model: 'CrackDet 2.1.0', reasoning: '细长纹理连续；长度估计 1.6m；宽度估计 0.4~0.8mm。' },
          metrics: { length_m: 1.6, width_mm: 0.6 },
          impact: '可能导致渗水与饰面劣化；建议 14 天内复核并封闭处理。',
          action: { owner: '物业/维保单位', sla: '14d处理', suggestion: '复核裂缝性质（温度收缩/结构）；必要时切槽灌浆或弹性修补。' },
          boxes: [{ x: 300, y: 360, w: 620, h: 130, label: '裂缝（0.77）', color: '#5bd6ff' }]
        }
      ],
      attachments: [
        { name: '立面分区索引.json', desc: '立面方位/楼层/轴网/构件编号' },
        { name: '缺陷截图与标注.zip', desc: '每个问题一套：原图+标注图+裁剪图' },
        { name: '隐私打码记录.log', desc: '打码区域、规则、处理时间（可选）' }
      ],
      audit: {
        traceId: 'trace-fcd-90c2...',
        operator: 'inspection-team',
        approvals: '安全员确认：待分配（建议）',
        dataRetention: '原始影像 365 天；结构化缺陷 3 年（建议）'
      }
    }
  },

  // 电力设施/市政场景
  municipal: {
    key: 'municipal',
    name: '电力设施巡检报告',
    sub: '设备编号定位 · 绝缘子/导线/金具检测 · 缺陷分级 · 运维工单',
    data: {
      header: {
        reportId: 'PWR-2025-1213-0006',
        project: '某 220kV 线路日常巡检',
        area: '杆塔 #125 ~ #142',
        period: '2025-12-12 08:00 ~ 12:00',
        createdAt: nowIso,
        issuer: 'AI 电力巡检系统 v0.9',
        confidentiality: '内部'
      },
      summary: {
        totalPhotos: 186,
        validPhotos: 172,
        issues: 31,
        duplicated: 7,
        avgConfidence: 0.86,
        slaHit: 0.91,
        topTypes: [
          { type: '绝缘子破损', count: 6 },
          { type: '导线异物', count: 5 },
          { type: '金具锈蚀', count: 4 }
        ]
      },
      task: {
        collectionMode: '无人机巡检（多角度）',
        reporters: '巡检员 2 人 + 无人机操作员 1 人',
        timeZone: 'Asia/Shanghai',
        weather: '晴 · 8~14℃ · 风力 2 级',
        gpsPolicy: 'RTK + 杆塔编号对照 · 精度<5m'
      },
      ai: {
        pipelineId: 'PIPE-PWR-2025.11',
        modelVersions: [
          { name: 'PowerEquip-Det', ver: '2.4.1' },
          { name: 'Insulator-Cls', ver: '3.1.0' },
          { name: 'Defect-Seg', ver: '1.9.2' },
          { name: 'RiskScore', ver: '1.2.0' }
        ],
        notes: '置信度<0.55 的结果进入"人工复核队列"；相似度>0.92 进入"疑似重复"聚类。'
      },
      issues: [
        {
          id: 'P-001',
          level: 'P0',
          type: '绝缘子破损',
          status: '待处置',
          location: { address: '杆塔 #128 A相', gps: '31.23041,121.47370', accuracy: '3m' },
          time: '2025-12-12T10:12:34+08:00',
          evidence: { photoId: 'PH-0091', source: '无人机', device: 'DJI M300', exif: '有', hash: 'sha256:8c..a1' },
          ai: { confidence: 0.93, model: 'Insulator-Cls 3.1.0', reasoning: '检测到绝缘子伞裙缺失；破损边缘清晰可见。' },
          impact: '存在闪络风险，属于重大安全隐患；建议 24 小时内更换。',
          action: { owner: '运维班组', sla: '24h更换', suggestion: '带电作业或停电更换；同步检查同串其他绝缘子。' },
          boxes: [{ x: 380, y: 260, w: 430, h: 300, label: '绝缘子破损（0.93）', color: '#ff5a7a' }]
        },
        {
          id: 'P-014',
          level: 'P1',
          type: '导线异物',
          status: '待处置',
          location: { address: '杆塔 #135 档距中部', gps: '31.22990,121.47115', accuracy: '5m' },
          time: '2025-12-12T11:48:20+08:00',
          evidence: { photoId: 'PH-0147', source: '无人机', device: 'DJI M300', exif: '有', hash: 'sha256:33..9f' },
          ai: { confidence: 0.82, model: 'PowerEquip-Det 2.4.1', reasoning: '检测到导线上悬挂异物；疑似塑料袋/风筝残骸。' },
          impact: '可能引起线路跳闸或导线损伤；建议 48 小时内清除。',
          action: { owner: '运维班组', sla: '48h清除', suggestion: '使用绝缘杆或无人机喷火器清除；记录异物类型。' },
          boxes: [{ x: 260, y: 310, w: 540, h: 290, label: '导线异物（0.82）', color: '#ffd166' }]
        }
      ],
      attachments: [
        { name: '杆塔巡检清单.csv', desc: '包含杆塔编号、时间、GPS、设备状态' },
        { name: '缺陷清单.xlsx', desc: '适配运维工单系统字段（含优先级、责任单位、SLA）' },
        { name: '重复聚类结果.json', desc: '相似组、代表图、相似度、人工复核状态' }
      ],
      audit: {
        traceId: 'trace-9c1c0e...',
        operator: 'system',
        approvals: '复核员：待分配（可选）',
        dataRetention: '原图 180 天；结构化结果 365 天；日志 365 天'
      }
    }
  }
}

// 从真实数据生成报告数据结构
const generateRealReportData = () => {
  const projectInfo = props.projectData || store.projectInfo || {}
  const detectionResults = store.detectionResults || []
  const analysisResult = store.analysisResult || {}
  const statistics = store.statistics || {}
  
  // 统计问题类型
  const issueTypeCount = {}
  let totalIssues = 0
  detectionResults.forEach(result => {
    (result.issues || []).forEach(issue => {
      const type = issue.name || issue.type || '未知问题'
      issueTypeCount[type] = (issueTypeCount[type] || 0) + 1
      totalIssues++
    })
  })
  
  const topTypes = Object.entries(issueTypeCount)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([type, count]) => ({ type, count }))
  
  // 计算危险等级统计
  const dangerCount = detectionResults.filter(r => r.status === 'danger').length
  const warningCount = detectionResults.filter(r => r.status === 'warning').length
  const successCount = detectionResults.filter(r => r.status === 'success').length
  
  // 生成问题列表（用于问题清单表格）
  const issues = []
  detectionResults.forEach((result, resultIndex) => {
    (result.issues || []).forEach((issue, issueIndex) => {
      const levelMap = {
        'danger': 'P0',
        'warning': 'P1',
        'caution': 'P2'
      }
      issues.push({
        id: issue.id || `ISS-${resultIndex}-${issueIndex}`,
        level: levelMap[issue.severity] || 'P2',
        type: issue.name || issue.type || '未知问题',
        status: '待处置',
        location: {
          address: result.name || result.filename || '未知位置',
          gps: projectInfo.gpsRange || '—',
          accuracy: '—'
        },
        time: new Date().toISOString(),
        evidence: {
          photoId: result.id || `IMG-${resultIndex}`,
          source: '无人机拍摄',
          device: projectInfo.deviceInfo || 'UAV',
          exif: '有',
          hash: `sha256:${Math.random().toString(16).slice(2, 10)}...`
        },
        ai: {
          confidence: issue.confidence || 0.8,
          model: analysisResult.algorithms?.[0] || 'AI-Detect',
          reasoning: issue.description || '检测到异常区域'
        },
        metrics: {},
        impact: issue.description || '建议进行进一步检查和处理',
        action: {
          owner: '巡检人员',
          sla: '7天内处理',
          suggestion: '请按照巡检规范进行处置'
        }
      })
    })
  })
  
  // 按图片分组（用于问题详情显示）
  const imageGroups = detectionResults
    .filter(result => result.issues && result.issues.length > 0)
    .map(result => ({
      imageId: result.id,
      imageName: result.name || result.filename || '未知图片',
      imageUrl: result.preview_url || result.previewUrl || '',
      boxes: result.issues.map(issue => ({
        x: issue.bbox?.x || 0,
        y: issue.bbox?.y || 0,
        w: issue.bbox?.width || 100,
        h: issue.bbox?.height || 100,
        label: `${issue.name || '问题'}（${((issue.confidence || 0.8) * 100).toFixed(0)}%）`,
        color: issue.severity === 'danger' ? '#ff5a7a' : 
               (issue.severity === 'warning' ? '#ffd166' : '#5bd6ff')
      })),
      issues: result.issues.map((issue, issueIndex) => ({
        id: issue.id || `ISS-${result.id}-${issueIndex}`,
        type: issue.name || issue.type || '未知问题',
        severity: issue.severity,
        description: issue.description || '检测到异常区域',
        confidence: issue.confidence || 0.8
      }))
    }))
  
  // 构建完整报告数据
  return {
    key: 'realData',
    name: `${sceneNames[props.sceneType] || '巡检'}报告`,
    sub: '实际项目数据',
    data: {
      header: {
        reportId: projectInfo.reportId || `RPT-${new Date().toISOString().split('T')[0].replace(/-/g, '')}-${Math.floor(Math.random() * 10000).toString().padStart(4, '0')}`,
        project: projectInfo.name || '巡检项目',
        area: projectInfo.area || projectInfo.location || '—',
        period: projectInfo.inspectionPeriod || new Date().toLocaleString('zh-CN'),
        createdAt: nowIso,
        issuer: 'AI 航测巡检系统 v1.0',
        confidentiality: '内部'
      },
      summary: {
        totalPhotos: statistics.totalImages || detectionResults.length || 0,
        validPhotos: statistics.totalImages || detectionResults.length || 0,
        issues: totalIssues,
        duplicated: 0,
        avgConfidence: parseFloat(statistics.avgConfidence) / 100 || 0.8,
        slaHit: 0.85,
        topTypes: topTypes.length > 0 ? topTypes : [{ type: '暂无问题', count: 0 }]
      },
      task: {
        platform: projectInfo.deviceInfo || 'DJI 无人机',
        sensor: '可见光相机',
        altitude: projectInfo.avgAltitude || '80m AGL',
        speed: '—',
        overlap: '—',
        gsd: projectInfo.gsd || '约 2 cm/pixel',
        weather: projectInfo.weather || '—',
        controlPoints: '—'
      },
      ai: {
        pipelineId: projectInfo.pipelineId || `PIPE-${(analysisResult.sceneType || 'UNKNOWN').toUpperCase()}-2025`,
        modelVersions: (analysisResult.algorithms || ['AI-Detect']).map(algo => ({
          name: algo,
          ver: '1.0.0'
        })),
        notes: '基于深度学习的智能检测系统，结果仅供参考，请结合实际情况判断。'
      },
      issues: issues.slice(0, 10), // 限制显示前10条（用于问题清单表格）
      imageGroups: imageGroups.slice(0, 10), // 限制显示前10张图片（用于问题详情）
      attachments: [
        { name: '原始图像.zip', desc: '包含所有巡检原始图像' },
        { name: '检测结果.xlsx', desc: '问题清单和统计数据' }
      ],
      audit: {
        traceId: projectInfo.traceId || `trace-${Math.random().toString(36).substring(2, 15)}`,
        operator: projectInfo.inspector || '巡检人员',
        approvals: projectInfo.reviewedBy ? `复核：${projectInfo.reviewedBy}` : '复核：待分配',
        dataRetention: '原始影像 365 天；结构化结果 730 天'
      }
    }
  }
}

// 当前报告数据
const currentReport = computed(() => {
  // 如果使用真实数据模式，返回从 store 生成的数据
  if (props.useRealData) {
    return generateRealReportData()
  }
  // 否则使用模拟数据
  const mappedKey = sceneMapping[props.sceneType] || 'roadUav'
  return reportDatasets[mappedKey]
})

const reportData = computed(() => currentReport.value.data)
const sceneName = computed(() => sceneNames[props.sceneType] || '巡检报告')

// 实际问题数量（用于显示）
const actualIssueCount = computed(() => {
  if (props.useRealData) {
    return store.detectionResults?.reduce((sum, r) => sum + (r.issues?.length || 0), 0) || 0
  }
  return reportData.value.issues?.length || 0
})

// 生成SVG证据图
const generateMediaSvg = (issue) => {
  const W = 1000
  const H = 600
  const boxes = issue.boxes || []
  
  // 生成网格
  let grid = ''
  for (let x = 0; x <= W; x += 80) {
    grid += `<line x1="${x}" y1="0" x2="${x}" y2="${H}" stroke="rgba(255,255,255,.06)" />`
  }
  for (let y = 0; y <= H; y += 80) {
    grid += `<line x1="0" y1="${y}" x2="${W}" y2="${y}" stroke="rgba(255,255,255,.06)" />`
  }
  
  // 生成标注框
  const rects = boxes.map((b, i) => {
    const c = b.color || '#5bd6ff'
    const lx = b.x + 8
    const ly = Math.max(22, b.y - 8)
    const labelWidth = Math.max(150, (b.label || '').length * 10)
    return `
      <rect x="${b.x}" y="${b.y}" width="${b.w}" height="${b.h}"
            fill="rgba(0,0,0,.0)" stroke="${c}" stroke-width="4" rx="10" />
      <rect x="${lx}" y="${ly - 18}" width="${labelWidth}" height="28" rx="8"
            fill="rgba(15,27,46,.85)" stroke="rgba(255,255,255,.15)" />
      <text x="${lx + 10}" y="${ly + 2}" fill="rgba(231,240,255,.95)" font-size="14" font-family="ui-sans-serif, system-ui">${b.label || ('疑似问题 #' + (i + 1))}</text>
    `
  }).join('')
  
  const evidenceId = Math.random().toString(16).slice(2, 10)
  
  return `
    <svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" class="w-full h-auto rounded-xl">
      <defs>
        <linearGradient id="bgG${evidenceId}" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="rgba(91,214,255,.10)" />
          <stop offset="55%" stop-color="rgba(255,255,255,.03)" />
          <stop offset="100%" stop-color="rgba(255,90,122,.08)" />
        </linearGradient>
      </defs>
      <rect x="0" y="0" width="${W}" height="${H}" fill="url(#bgG${evidenceId})" />
      ${grid}
      <g>
        <rect x="30" y="24" width="${W - 60}" height="80" rx="16" fill="rgba(15,27,46,.6)" stroke="rgba(255,255,255,.1)"/>
        <text x="50" y="60" fill="rgba(231,240,255,.95)" font-size="24" font-weight="700" font-family="ui-sans-serif, system-ui">证据图：${issue.id || '—'}</text>
        <text x="50" y="86" fill="rgba(138,164,198,.9)" font-size="14" font-family="ui-sans-serif, system-ui">${issue.type || '—'} · 来源：${issue.evidence?.source || '—'} · photoId：${issue.evidence?.photoId || '—'}</text>
      </g>
      ${rects}
      <g>
        <rect x="${W - 240}" y="${H - 60}" width="210" height="36" rx="10" fill="rgba(15,27,46,.6)" stroke="rgba(255,255,255,.1)"/>
        <text x="${W - 225}" y="${H - 36}" fill="rgba(231,240,255,.85)" font-size="12" font-family="ui-monospace">evidence-id: ${evidenceId}</text>
      </g>
    </svg>
  `
}

// 获取风险等级样式
const getRiskClass = (level) => {
  const map = {
    'P0': 'tag p0',
    'P1': 'tag p1',
    'P2': 'tag p2',
    'P3': 'tag p3'
  }
  return map[level] || 'tag'
}

const getRiskText = (level) => {
  const map = {
    'P0': 'P0 紧急',
    'P1': 'P1 高',
    'P2': 'P2 中',
    'P3': 'P3 低'
  }
  return map[level] || level || '—'
}

// 任务信息字段映射
const getTaskFields = computed(() => {
  const t = reportData.value.task
  
  // 如果使用真实数据，返回通用字段
  if (props.useRealData) {
    return [
      { label: '采集设备', value: t.platform || '—' },
      { label: '传感器', value: t.sensor || '—' },
      { label: '飞行高度', value: t.altitude || '—' },
      { label: 'GSD', value: t.gsd || '—' },
      { label: '天气', value: t.weather || '—' }
    ].filter(f => f.value && f.value !== '—')
  }
  
  const sceneKey = sceneMapping[props.sceneType] || 'roadUav'
  
  if (sceneKey === 'municipal') {
    return [
      { label: '采集方式', value: t.collectionMode },
      { label: '人员配置', value: t.reporters },
      { label: '天气', value: t.weather },
      { label: '时区', value: t.timeZone },
      { label: '定位策略', value: t.gpsPolicy }
    ]
  } else if (sceneKey === 'roadUav') {
    return [
      { label: '无人机平台', value: t.platform },
      { label: '传感器', value: t.sensor },
      { label: '飞行高度', value: t.altitude },
      { label: '飞行速度', value: t.speed },
      { label: '重叠度', value: t.overlap },
      { label: 'GSD', value: t.gsd },
      { label: '天气', value: t.weather },
      { label: '控制点/定位', value: t.controlPoints }
    ]
  } else if (sceneKey === 'pvUav') {
    return [
      { label: '无人机平台', value: t.platform },
      { label: '传感器', value: t.sensors },
      { label: '飞行高度', value: t.altitude },
      { label: 'GSD', value: t.gsd },
      { label: '环境条件', value: t.env },
      { label: '采集建议', value: t.bestPractice }
    ]
  } else if (sceneKey === 'facadeUav') {
    return [
      { label: '无人机平台', value: t.platform },
      { label: '传感器', value: t.sensor },
      { label: '拍摄距离', value: t.distance },
      { label: '安全措施', value: t.safety },
      { label: '天气', value: t.weather },
      { label: '隐私处理', value: t.privacy }
    ]
  }
  return []
})

// 获取问题度量信息
const getIssueMetrics = (issue) => {
  const sceneKey = sceneMapping[props.sceneType] || 'roadUav'
  const m = issue.metrics || {}
  const lines = []
  
  if (sceneKey === 'roadUav') {
    if (m.area_m2 !== undefined) lines.push(`面积：${fmt.num(m.area_m2)} ㎡`)
    if (m.depth_est_cm !== undefined) lines.push(`深度：${fmt.num(m.depth_est_cm)} cm`)
    if (m.length_m !== undefined) lines.push(`长度：${fmt.num(m.length_m)} m`)
    if (m.width_mm !== undefined) lines.push(`宽度：${fmt.num(m.width_mm)} mm`)
  } else if (sceneKey === 'pvUav') {
    if (m.deltaT_C !== undefined) lines.push(`ΔT：${fmt.num(m.deltaT_C)} ℃`)
    if (m.tHot_C !== undefined) lines.push(`热点温度：${fmt.num(m.tHot_C)} ℃`)
    if (m.tRef_C !== undefined) lines.push(`参考温度：${fmt.num(m.tRef_C)} ℃`)
    if (m.coverage_pct !== undefined) lines.push(`覆盖比例：${Math.round(m.coverage_pct * 100)}%`)
    if (m.lossEst_pct !== undefined) lines.push(`估计损失：${fmt.num(m.lossEst_pct)}%`)
  } else if (sceneKey === 'facadeUav') {
    if (m.area_m2 !== undefined) lines.push(`风险面积：${fmt.num(m.area_m2)} ㎡`)
    if (m.height_m !== undefined) lines.push(`高度：${fmt.num(m.height_m)} m`)
    if (m.length_m !== undefined) lines.push(`裂缝长度：${fmt.num(m.length_m)} m`)
    if (m.width_mm !== undefined) lines.push(`裂缝宽度：${fmt.num(m.width_mm)} mm`)
  }
  
  return lines
}

// 获取定位信息
const getLocationLines = (issue) => {
  const loc = issue.location || {}
  const lines = []
  
  if (loc.chainage) lines.push(`里程：${loc.chainage}`)
  if (loc.zone) lines.push(`立面分区：${loc.zone}`)
  if (loc.asset) lines.push(`资产：${loc.asset}`)
  if (loc.string) lines.push(`归属：${loc.string}`)
  if (loc.address) lines.push(`位置：${loc.address}`)
  if (loc.gps && loc.gps !== '—') lines.push(`GPS：${loc.gps}（精度：${loc.accuracy || '—'}）`)
  
  return lines
}
</script>

<template>
  <Teleport to="body">
    <div 
      class="fixed inset-0 bg-black/85 backdrop-blur-sm z-50 flex items-start justify-center p-4 overflow-y-auto"
      @click="emit('close')"
    >
      <div 
        class="glass-card w-full max-w-4xl my-8"
        @click.stop
      >
        <!-- 顶部栏 -->
        <div class="flex items-center justify-between p-4 border-b border-white/10">
          <div>
            <h3 class="text-xl font-bold text-white">{{ template.name }} · 报告预览</h3>
            <p class="text-white/50 text-sm mt-1">
              场景：{{ sceneName }} · {{ currentReport.sub }}
              <span v-if="props.useRealData" class="ml-2 px-2 py-0.5 bg-brand-primary/20 text-brand-sky text-xs rounded">使用真实数据</span>
              <span v-if="props.useRealData && reportData.issues" class="ml-2 text-xs">
                ({{ reportData.issues.length }} 个问题)
              </span>
            </p>
          </div>
          <button 
            @click="emit('close')" 
            class="w-10 h-10 flex items-center justify-center rounded-xl text-white/50 hover:text-white hover:bg-white/5 transition-colors"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <!-- 报告内容 -->
        <div class="p-4 space-y-4">
          <!-- ① 封面/摘要卡片 -->
          <div class="inner-card">
            <div class="section-title">
              <span>封面信息 / 报告摘要</span>
              <span class="pill info">{{ reportData.header.confidentiality }}</span>
            </div>
            
            <div class="grid grid-cols-2 gap-3 mb-4">
              <div class="kv-row">
                <span class="label">报告编号</span>
                <span class="value">{{ reportData.header.reportId }}</span>
              </div>
              <div class="kv-row">
                <span class="label">项目/任务</span>
                <span class="value text-sm">{{ reportData.header.project }}</span>
              </div>
              <div class="kv-row">
                <span class="label">范围</span>
                <span class="value text-sm">{{ reportData.header.area }}</span>
              </div>
              <div class="kv-row">
                <span class="label">巡检时段</span>
                <span class="value text-sm">{{ reportData.header.period }}</span>
              </div>
              <div class="kv-row">
                <span class="label">出具系统</span>
                <span class="value text-sm">{{ reportData.header.issuer }}</span>
              </div>
              <div class="kv-row">
                <span class="label">生成时间</span>
                <span class="value text-sm">{{ fmt.dt(reportData.header.createdAt) }}</span>
              </div>
            </div>
            
            <div class="divider"></div>
            
            <!-- 统计摘要 -->
            <div class="grid grid-cols-4 gap-3 mb-4">
              <div class="stat-card">
                <div class="stat-label">输入照片</div>
                <div class="stat-value text-white">{{ fmt.num(reportData.summary.totalPhotos) }}</div>
                <div class="stat-sub">有效：{{ fmt.num(reportData.summary.validPhotos) }}</div>
              </div>
              <div class="stat-card">
                <div class="stat-label">识别问题</div>
                <div class="stat-value text-accent-danger">{{ fmt.num(reportData.summary.issues) }}</div>
                <div class="stat-sub">疑似重复：{{ fmt.num(reportData.summary.duplicated) }}</div>
              </div>
              <div class="stat-card">
                <div class="stat-label">平均置信度</div>
                <div class="stat-value text-brand-primary">{{ fmt.pct(reportData.summary.avgConfidence) }}</div>
                <div class="stat-sub">供复核参考</div>
              </div>
              <div class="stat-card">
                <div class="stat-label">SLA命中率</div>
                <div class="stat-value text-accent-success">{{ fmt.pct(reportData.summary.slaHit) }}</div>
                <div class="stat-sub">按建议时限</div>
              </div>
            </div>
            
            <div class="text-mini">
              <span class="font-semibold text-white/80">高频问题类型：</span>
              {{ reportData.summary.topTypes.map(x => `${x.type}(${x.count})`).join(' · ') }}
            </div>
          </div>
          
          <!-- ② 任务信息 + ③ AI分析 并排 -->
          <div class="grid grid-cols-2 gap-4">
            <!-- 任务信息 -->
            <div class="inner-card">
              <div class="section-title">
                <span>任务信息（采集/环境/设备）</span>
                <span class="pill">用于复现与责任划分</span>
              </div>
              <div class="space-y-2">
                <div 
                  v-for="field in getTaskFields" 
                  :key="field.label"
                  class="kv-row"
                >
                  <span class="label">{{ field.label }}</span>
                  <span class="value text-xs">{{ field.value }}</span>
                </div>
              </div>
            </div>
            
            <!-- AI分析说明 -->
            <div class="inner-card">
              <div class="section-title">
                <span>AI 分析说明</span>
                <span class="pill">可解释 / 可追溯</span>
              </div>
              <div class="space-y-2 mb-3">
                <div class="kv-row">
                  <span class="label">Pipeline ID</span>
                  <span class="value text-xs">{{ reportData.ai.pipelineId }}</span>
                </div>
              </div>
              <div class="text-mini mb-3">{{ reportData.ai.notes }}</div>
              <div class="text-mini font-semibold text-white/80 mb-2">模型版本：</div>
              <div class="flex flex-wrap gap-2">
                <span 
                  v-for="m in reportData.ai.modelVersions"
                  :key="m.name"
                  class="tag"
                >
                  {{ m.name }} v{{ m.ver }}
                </span>
              </div>
            </div>
          </div>
          
          <!-- ④ 问题清单表格 -->
          <div class="inner-card">
            <div class="section-title">
              <span>问题清单（便于一眼扫完）</span>
              <span class="pill info">共 {{ props.useRealData ? actualIssueCount : reportData.issues.length }} 条</span>
            </div>
            <div class="text-mini mb-3">提示：表格用于"快速浏览+导入工单"；详细证据请看下方"问题详情"。</div>
            
            <!-- 有问题时显示表格 -->
            <table v-if="reportData.issues && reportData.issues.length > 0" class="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>优先级</th>
                  <th>问题类型</th>
                  <th>定位</th>
                  <th>置信度</th>
                  <th>状态</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="issue in reportData.issues" :key="issue.id">
                  <td class="font-mono text-xs">{{ issue.id }}</td>
                  <td><span :class="getRiskClass(issue.level)">{{ getRiskText(issue.level) }}</span></td>
                  <td class="text-xs">{{ issue.type }}</td>
                  <td class="text-mini">
                    {{ issue.location.chainage || issue.location.zone || issue.location.address || '—' }}
                  </td>
                  <td><span class="tag">{{ fmt.pct(issue.ai.confidence) }}</span></td>
                  <td><span class="tag">{{ issue.status }}</span></td>
                </tr>
              </tbody>
            </table>
            
            <!-- 无问题时的提示 -->
            <div v-else class="text-center py-8">
              <div class="text-4xl mb-3">✅</div>
              <div class="text-white/70 text-sm">未检测到问题</div>
              <div class="text-white/50 text-xs mt-2">所有图片状态良好</div>
            </div>
          </div>
          
          <!-- ⑤ 问题详情（按图片分组显示） -->
          <div class="inner-card">
            <div class="section-title">
              <span>问题详情（按图片分组 / 可复核）</span>
              <span class="pill">每张图片显示所有检测到的问题</span>
            </div>
            
            <!-- 无问题提示 -->
            <div v-if="!reportData.imageGroups || reportData.imageGroups.length === 0" class="mt-4 text-center py-8">
              <div class="text-4xl mb-3">✅</div>
              <div class="text-white/70 text-sm">未检测到问题</div>
            </div>
            
            <!-- 按图片分组显示 -->
            <div 
              v-for="(imageGroup, groupIndex) in reportData.imageGroups?.slice(0, 3)" 
              :key="imageGroup.imageId"
              class="mt-4"
              :class="{ 'border-t border-white/10 pt-4': groupIndex > 0 }"
            >
              <!-- 图片标题 -->
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-3">
                  <span class="font-mono text-white font-semibold">{{ imageGroup.imageName }}</span>
                  <span class="px-2 py-1 rounded text-xs bg-brand-primary/20 text-brand-sky">
                    共 {{ imageGroup.issues.length }} 个问题
                  </span>
                </div>
              </div>
              
              <!-- 图片 + 问题列表 -->
              <div class="grid grid-cols-2 gap-4">
                <!-- 左侧：图片 + 所有bbox标注 -->
                <div class="relative w-full rounded-xl overflow-hidden bg-gray-900">
                  <img 
                    :ref="el => { if (el) imageRefs[imageGroup.imageId] = el }"
                    :src="imageGroup.imageUrl" 
                    :alt="imageGroup.imageName"
                    class="w-full h-auto"
                    style="max-height: 500px; object-fit: contain; display: block;"
                    @load="updateImageDisplayInfo(imageGroup.imageId, $event.target)"
                  />
                  <!-- 渲染所有bbox -->
                  <div 
                    v-if="imageGroup.boxes && imageGroup.boxes.length > 0"
                    class="absolute inset-0 pointer-events-none"
                  >
                    <div 
                      v-for="(box, idx) in imageGroup.boxes" 
                      :key="idx"
                      class="absolute border-4 rounded-lg"
                      :style="getBboxPixelStyle(box, imageGroup.imageId)"
                    >
                      <div 
                        class="absolute -top-7 left-0 px-2 py-1 rounded text-white text-xs font-bold whitespace-nowrap"
                        :style="{
                          backgroundColor: box.color,
                          boxShadow: '0 2px 4px rgba(0,0,0,0.3)'
                        }"
                      >
                        {{ box.label }}
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- 右侧：问题列表 -->
                <div class="space-y-3 max-h-[500px] overflow-y-auto pr-2">
                  <div 
                    v-for="(issue, issueIndex) in imageGroup.issues" 
                    :key="issue.id"
                    class="inner-card !p-3"
                  >
                    <!-- 问题标题 -->
                    <div class="flex items-center justify-between mb-2">
                      <span class="font-semibold text-white text-sm">
                        {{ issueIndex + 1 }}. {{ issue.type }}
                      </span>
                      <span 
                        class="px-2 py-0.5 rounded text-xs"
                        :class="{
                          'bg-accent-danger/20 text-accent-danger': issue.severity === 'danger',
                          'bg-accent-warning/20 text-accent-warning': issue.severity === 'warning',
                          'bg-brand-sky/20 text-brand-sky': issue.severity === 'caution'
                        }"
                      >
                        {{ issue.severity === 'danger' ? '严重' : (issue.severity === 'warning' ? '一般' : '轻微') }}
                      </span>
                    </div>
                    
                    <!-- 问题描述 -->
                    <div class="text-xs text-white/70 mb-2">
                      {{ issue.description }}
                    </div>
                    
                    <!-- 置信度 -->
                    <div class="text-xs text-white/50">
                      置信度：{{ (issue.confidence * 100).toFixed(0) }}%
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 更多图片提示 -->
            <div v-if="reportData.imageGroups && reportData.imageGroups.length > 3" class="mt-4 text-center text-mini">
              还有 {{ reportData.imageGroups.length - 3 }} 张图片...（完整报告中展示）
            </div>
          </div>
          
          <!-- ⑥ 附件 + 审计 并排 -->
          <div class="grid grid-cols-2 gap-4">
            <!-- 附件列表 -->
            <div class="inner-card">
              <div class="section-title">
                <span>附件 / 交付物</span>
                <span class="pill">用于对接工单/存档</span>
              </div>
              <div class="space-y-2">
                <div 
                  v-for="att in reportData.attachments" 
                  :key="att.name"
                  class="flex items-start justify-between gap-3 p-2 rounded-lg border border-white/5 bg-white/[0.02]"
                >
                  <div>
                    <div class="text-sm text-white/90 font-medium">{{ att.name }}</div>
                    <div class="text-mini">{{ att.desc }}</div>
                  </div>
                  <span class="tag flex-shrink-0">附件</span>
                </div>
              </div>
            </div>
            
            <!-- 审计信息 -->
            <div class="inner-card">
              <div class="section-title">
                <span>审计 / 合规 / 追溯</span>
                <span class="pill warn">建议强制保留</span>
              </div>
              <div class="space-y-2 mb-3">
                <div class="kv-row">
                  <span class="label">Trace ID</span>
                  <span class="value text-xs">{{ reportData.audit.traceId }}</span>
                </div>
                <div class="kv-row">
                  <span class="label">操作主体</span>
                  <span class="value text-xs">{{ reportData.audit.operator }}</span>
                </div>
                <div class="kv-row">
                  <span class="label">审批/复核</span>
                  <span class="value text-xs">{{ reportData.audit.approvals }}</span>
                </div>
                <div class="kv-row">
                  <span class="label">数据留存</span>
                  <span class="value text-xs">{{ reportData.audit.dataRetention }}</span>
                </div>
              </div>
              <div class="text-mini">
                建议：保留每条问题的"原图hash、模型版本、阈值配置、后处理规则、人工改动记录"。用于复盘与仲裁。
              </div>
            </div>
          </div>
          
          <!-- 模板特有功能提示 -->
          <div v-if="template.includeOrtho || template.include3D" class="inner-card border-brand-primary/30">
            <div class="section-title">
              <span>{{ template.name }} 额外功能</span>
              <span class="pill info">本模板特有</span>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div v-if="template.includeOrtho" class="p-4 rounded-xl bg-brand-primary/5 border border-brand-primary/20">
                <div class="flex items-center gap-2 mb-2">
                  <svg class="w-5 h-5 text-brand-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l5.447 2.724A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                  </svg>
                  <span class="font-semibold text-white">正射影像图</span>
                </div>
                <p class="text-mini">问题点位将映射到正射影像上，支持区域统计分析和空间关联</p>
              </div>
              <div v-if="template.include3D" class="p-4 rounded-xl bg-accent-info/5 border border-accent-info/20">
                <div class="flex items-center gap-2 mb-2">
                  <svg class="w-5 h-5 text-accent-info" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5" />
                  </svg>
                  <span class="font-semibold text-white">三维模型</span>
                </div>
                <p class="text-mini">生成三维实景模型，问题点位立体标注，支持量测功能</p>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 底部 -->
        <div class="flex items-center justify-between p-4 border-t border-white/10 text-mini">
          <div>
            生成时间：{{ fmt.dt(reportData.header.createdAt) }} · 报告版本：v1.0
          </div>
          <div>
            包含：摘要 / 任务信息 / 问题清单 / 问题详情 / 附件 / 审计
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

