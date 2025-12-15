"""
报告相关路由
"""
from fastapi import APIRouter, HTTPException
from typing import Optional

from services.mock_ai import mock_ai
from database import get_db
from models.schemas import TemplateSelectRequest, DetectionResultUpdate

router = APIRouter()


@router.get("/templates/{scene_type}")
async def get_templates(scene_type: str):
    """
    获取指定场景的报告模板列表
    """
    templates = mock_ai.get_report_templates(scene_type)
    return {"scene_type": scene_type, "templates": templates}


@router.post("/select-template")
async def select_template(request: TemplateSelectRequest):
    """
    为项目选择报告模板
    """
    # 更新项目的模板选择
    async with get_db() as db:
        cursor = await db.execute(
            "UPDATE projects SET template_id = ?, status = ? WHERE id = ?",
            (request.template_id, "template_selected", request.project_id)
        )
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        await db.commit()
    
    return {"message": "模板已选择", "template_id": request.template_id}


@router.post("/detect/{project_id}")
async def run_detection(project_id: str):
    """
    执行AI检测
    """
    # 获取项目信息
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT scene_type FROM projects WHERE id = ?",
            (project_id,)
        )
        project = await cursor.fetchone()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        scene_type = project["scene_type"] or "building"
        
        # 获取项目图片
        cursor = await db.execute(
            "SELECT id, filename FROM images WHERE project_id = ?",
            (project_id,)
        )
        images = await cursor.fetchall()
        
        if not images:
            raise HTTPException(status_code=400, detail="项目没有图片")
    
    # 对每张图片执行检测
    results = []
    for img in images:
        detection = mock_ai.detect_issues(img["id"], scene_type)
        detection["filename"] = img["filename"]
        detection["preview_url"] = f"/uploads/{project_id}/{img['filename']}"
        results.append(detection)
        
        # 保存检测结果到数据库
        async with get_db() as db:
            await db.execute(
                """INSERT OR REPLACE INTO detection_results 
                   (id, image_id, project_id, confidence, status, suggestion)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (f"det-{img['id']}", img["id"], project_id, 
                 detection["confidence"], detection["status"], detection["suggestion"])
            )
            
            # 保存问题详情
            for issue in detection["issues"]:
                await db.execute(
                    """INSERT INTO issues 
                       (id, detection_id, issue_type, name, severity, description, confidence,
                        bbox_x, bbox_y, bbox_width, bbox_height)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (issue["id"], f"det-{img['id']}", issue["type"], issue["name"],
                     issue["severity"], issue["description"], issue["confidence"],
                     issue["bbox"]["x"], issue["bbox"]["y"], 
                     issue["bbox"]["width"], issue["bbox"]["height"])
                )
            
            await db.commit()
    
    # 更新项目状态
    async with get_db() as db:
        await db.execute(
            "UPDATE projects SET status = ? WHERE id = ?",
            ("detected", project_id)
        )
        await db.commit()
    
    # 计算统计信息
    total = len(results)
    danger_count = sum(1 for r in results if r["status"] == "danger")
    warning_count = sum(1 for r in results if r["status"] == "warning")
    success_count = sum(1 for r in results if r["status"] == "success")
    total_issues = sum(len(r["issues"]) for r in results)
    avg_confidence = sum(r["confidence"] for r in results) / total if total > 0 else 0
    
    return {
        "project_id": project_id,
        "results": results,
        "statistics": {
            "total_images": total,
            "danger_count": danger_count,
            "warning_count": warning_count,
            "success_count": success_count,
            "total_issues": total_issues,
            "avg_confidence": round(avg_confidence, 2)
        }
    }


@router.get("/detection-results/{project_id}")
async def get_detection_results(project_id: str):
    """
    获取项目的检测结果
    """
    async with get_db() as db:
        # 获取检测结果
        cursor = await db.execute(
            """SELECT dr.*, i.filename, i.original_name
               FROM detection_results dr
               JOIN images i ON dr.image_id = i.id
               WHERE dr.project_id = ?""",
            (project_id,)
        )
        detection_rows = await cursor.fetchall()
        
        if not detection_rows:
            raise HTTPException(status_code=404, detail="没有检测结果")
        
        results = []
        for det in detection_rows:
            # 获取该检测结果的问题
            cursor = await db.execute(
                "SELECT * FROM issues WHERE detection_id = ?",
                (det["id"],)
            )
            issue_rows = await cursor.fetchall()
            
            issues = [
                {
                    "id": issue["id"],
                    "type": issue["issue_type"],
                    "name": issue["name"],
                    "severity": issue["severity"],
                    "description": issue["description"],
                    "confidence": issue["confidence"],
                    "bbox": {
                        "x": issue["bbox_x"],
                        "y": issue["bbox_y"],
                        "width": issue["bbox_width"],
                        "height": issue["bbox_height"]
                    }
                }
                for issue in issue_rows
            ]
            
            results.append({
                "id": det["id"],
                "image_id": det["image_id"],
                "filename": det["filename"],
                "preview_url": f"/uploads/{project_id}/{det['filename']}",
                "confidence": det["confidence"],
                "status": det["status"],
                "issues": issues,
                "suggestion": det["suggestion"]
            })
        
        return {"project_id": project_id, "results": results}


@router.put("/detection-result/{project_id}/{image_id}")
async def update_detection_result(project_id: str, image_id: str, update: DetectionResultUpdate):
    """
    更新单张图片的检测结果
    用于用户手动修正
    """
    async with get_db() as db:
        # 获取检测结果ID
        cursor = await db.execute(
            "SELECT id FROM detection_results WHERE project_id = ? AND image_id = ?",
            (project_id, image_id)
        )
        det = await cursor.fetchone()
        
        if not det:
            raise HTTPException(status_code=404, detail="检测结果不存在")
        
        detection_id = det["id"]
        
        # 删除旧的问题记录
        await db.execute("DELETE FROM issues WHERE detection_id = ?", (detection_id,))
        
        # 插入新的问题记录
        for issue in update.issues:
            await db.execute(
                """INSERT INTO issues 
                   (id, detection_id, issue_type, name, severity, description, confidence,
                    bbox_x, bbox_y, bbox_width, bbox_height)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (issue.id, detection_id, issue.type, issue.name,
                 issue.severity, issue.description, issue.confidence,
                 issue.bbox.x, issue.bbox.y, issue.bbox.width, issue.bbox.height)
            )
        
        # 更新检测结果
        new_status = "success"
        if update.issues:
            new_status = "danger" if any(i.severity == "danger" for i in update.issues) else "warning"
        
        await db.execute(
            "UPDATE detection_results SET status = ?, suggestion = ? WHERE id = ?",
            (new_status, update.suggestion or "", detection_id)
        )
        
        await db.commit()
    
    return {"message": "检测结果已更新"}

