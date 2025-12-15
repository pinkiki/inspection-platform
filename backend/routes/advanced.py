"""
进阶处理相关路由
"""
from fastapi import APIRouter, HTTPException
from typing import Dict
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/advanced", tags=["advanced"])

# 简单的内存存储，实际应该使用数据库
# 格式: {task_id: {status, stage, progress, created_at}}
tasks_store: Dict[str, Dict] = {}


@router.post("/start")
async def start_advanced_task(project_id: str, template_type: str):
    """启动进阶处理任务"""
    task_id = str(uuid.uuid4())
    
    tasks_store[task_id] = {
        "task_id": task_id,
        "project_id": project_id,
        "template_type": template_type,
        "status": "processing",
        "stage": "aerial_triangulation",
        "progress": 0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    return {
        "task_id": task_id,
        "status": "started",
        "message": "进阶处理任务已启动"
    }


@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    if task_id not in tasks_store:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return tasks_store[task_id]


@router.post("/skip-stage")
async def skip_stage(task_id: str):
    """管理员：跳过当前阶段（仅开发模式）"""
    if task_id not in tasks_store:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = tasks_store[task_id]
    
    # 这里应该有实际的阶段跳过逻辑
    # 简单演示：直接标记为完成
    task["status"] = "completed"
    task["progress"] = 100
    task["updated_at"] = datetime.now().isoformat()
    
    return {
        "success": True,
        "message": "已跳过当前阶段"
    }


@router.post("/complete")
async def complete_task(task_id: str):
    """完成任务"""
    if task_id not in tasks_store:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = tasks_store[task_id]
    task["status"] = "completed"
    task["progress"] = 100
    task["updated_at"] = datetime.now().isoformat()
    
    return {
        "success": True,
        "message": "任务已完成"
    }

