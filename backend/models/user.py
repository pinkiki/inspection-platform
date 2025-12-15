from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class UserInfo(BaseModel):
    id: int
    name: str
    email: str
    avatar: Optional[str] = None
    join_date: str
    total_projects: int
    total_reports: int
    last_login: str

class CreditRecord(BaseModel):
    id: int
    user_id: int
    type: str  # 'earn' or 'spend'
    amount: int
    reason: str
    timestamp: datetime

class StepSnapshot(BaseModel):
    id: int
    user_id: int
    step: int
    step_name: str
    timestamp: datetime
    image_count: int
    template_name: str
    data: dict  # 包含完整的状态数据

class UserProfile(BaseModel):
    user_info: UserInfo
    current_credits: int
    total_used: int
    total_earned: int
    level: str
    next_level_info: Optional[dict]
    credit_history: List[CreditRecord]
    step_snapshots: List[StepSnapshot]