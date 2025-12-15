"""
Pydantic数据模型
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime, date


# ============ 上传相关 ============

class ImageInfo(BaseModel):
    id: str
    filename: str
    original_name: str
    file_path: str
    file_size: int
    width: Optional[int] = None
    height: Optional[int] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    preview_url: str


class UploadResponse(BaseModel):
    project_id: str
    images: List[ImageInfo]
    total_count: int
    total_size: int


# ============ 场景分析相关 ============

class Algorithm(BaseModel):
    id: str
    name: str
    description: str


class SceneAnalysisResult(BaseModel):
    scene_type: str
    scene_name: str
    confidence: float
    algorithms: List[str]
    description: str


class SceneType(BaseModel):
    id: str
    name: str
    icon: str
    confidence: float
    description: str
    algorithms: List[str]


# ============ 报告模板相关 ============

class ReportTemplate(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    features: List[str]
    include_ortho: bool
    include_3d: bool
    estimated_time: str
    price: str
    recommended: bool = False


class TemplateSelectRequest(BaseModel):
    project_id: str
    template_id: str


# ============ 检测结果相关 ============

class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float


class Issue(BaseModel):
    id: str
    type: str
    name: str
    severity: str  # danger, warning, caution
    description: str
    confidence: float
    bbox: BoundingBox


class DetectionResult(BaseModel):
    id: str
    image_id: str
    filename: str
    preview_url: str
    confidence: float
    status: str  # danger, warning, success
    issues: List[Issue]
    gps: Optional[dict] = None
    suggestion: str


class DetectionResultUpdate(BaseModel):
    issues: List[Issue]
    suggestion: Optional[str] = None


# ============ 进阶报告相关 ============

class AdvancedReportStatus(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    ortho_status: str  # pending, processing, completed
    ortho_progress: float
    model_3d_status: str
    model_3d_progress: float


class IssuePoint(BaseModel):
    id: str
    x: float
    y: float
    status: str
    issues_count: int


# ============ 导出相关 ============

class ProjectInfo(BaseModel):
    name: str
    location: Optional[str] = None
    inspection_date: Optional[str] = None
    inspector: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


class DeviceInfo(BaseModel):
    drone_model: Optional[str] = None
    camera_model: Optional[str] = None
    flight_altitude: Optional[str] = None
    flight_date: Optional[str] = None


class ExportRequest(BaseModel):
    format: str  # pdf, word


class ExportResponse(BaseModel):
    download_url: str
    filename: str


# ============ 积分系统相关 ============

class CreditTransaction(BaseModel):
    id: int
    amount: int  # 正数为增加，负数为扣除
    reason: str
    balance: int
    timestamp: str


class UserCredits(BaseModel):
    user_id: str
    credits: int
    history: List[CreditTransaction]


class DeductCreditsRequest(BaseModel):
    amount: int
    reason: str


class DeductCreditsResponse(BaseModel):
    success: bool
    new_balance: int
    message: Optional[str] = None


class CreditsHistoryResponse(BaseModel):
    history: List[CreditTransaction]
    current_balance: int

