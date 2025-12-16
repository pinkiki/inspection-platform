from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class StepSnapshot(BaseModel):
    """步骤快照模型"""
    id: Optional[int] = None
    user_id: int
    step_index: int = Field(..., description="当前步骤索引 (0-5)")
    step_route: str = Field(..., description="当前步骤路由路径")
    snapshot_data: Dict[str, Any] = Field(..., description="该步骤及之前的所有业务数据")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    name: Optional[str] = Field(None, max_length=100, description="快照名称")
    description: Optional[str] = Field(None, max_length=500, description="快照描述")

    class Config:
        from_attributes = True


class StepSnapshotCreate(BaseModel):
    """创建步骤快照请求"""
    step_index: int = Field(..., ge=0, le=5, description="当前步骤索引 (0-5)")
    step_route: str = Field(..., description="当前步骤路由路径")
    snapshot_data: Dict[str, Any] = Field(..., description="该步骤及之前的所有业务数据")
    name: Optional[str] = Field(None, max_length=100, description="快照名称")
    description: Optional[str] = Field(None, max_length=500, description="快照描述")


class StepSnapshotResponse(BaseModel):
    """步骤快照响应"""
    id: int
    step_index: int
    step_route: str
    created_at: datetime
    updated_at: datetime
    name: Optional[str]
    description: Optional[str]

    class Config:
        from_attributes = True


class SnapshotListItem(BaseModel):
    """快照列表项"""
    id: int
    step_index: int
    step_route: str
    step_name: str = Field(..., description="步骤显示名称")
    created_at: datetime
    name: Optional[str]

    class Config:
        from_attributes = True


# 步骤索引到名称的映射
STEP_NAMES = {
    0: "图片上传",
    1: "场景分析",
    2: "报告模板",
    3: "识别审核",
    4: "进阶报告",
    5: "报告导出"
}

# 步骤路由映射
STEP_ROUTES = {
    0: "/",
    1: "/analysis",
    2: "/template",
    3: "/review",
    4: "/advanced",
    5: "/export"
}