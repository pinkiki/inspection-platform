"""
上传相关路由
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import uuid
import os

from services.file_handler import FileHandler
from database import get_db

router = APIRouter()

# 初始化文件处理器
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
file_handler = FileHandler(UPLOAD_DIR)


@router.post("/images")
async def upload_images(files: List[UploadFile] = File(...)):
    """
    上传图片
    支持多张图片批量上传
    """
    if not files:
        raise HTTPException(status_code=400, detail="没有上传文件")
    
    # 生成项目ID
    project_id = f"PRJ-{uuid.uuid4().hex[:12].upper()}"
    
    uploaded_images = []
    total_size = 0
    
    for file in files:
        # 检查文件类型
        if not file_handler.is_allowed_file(file.filename):
            continue
        
        try:
            # 读取文件内容
            content = await file.read()
            
            # 保存文件
            image_info = await file_handler.save_file(content, project_id, file.filename)
            uploaded_images.append(image_info)
            total_size += image_info["file_size"]
            
        except ValueError as e:
            # 跳过不合法的文件
            continue
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    
    if not uploaded_images:
        raise HTTPException(status_code=400, detail="没有有效的图片文件")
    
    # 保存项目信息到数据库
    async with get_db() as db:
        await db.execute(
            "INSERT INTO projects (id, status) VALUES (?, ?)",
            (project_id, "uploaded")
        )
        
        for img in uploaded_images:
            await db.execute(
                """INSERT INTO images (id, project_id, filename, original_name, file_path, file_size, width, height)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (img["id"], project_id, img["filename"], img["original_name"], 
                 img["file_path"], img["file_size"], img["width"], img["height"])
            )
        
        await db.commit()
    
    return {
        "project_id": project_id,
        "images": uploaded_images,
        "total_count": len(uploaded_images),
        "total_size": total_size
    }


@router.get("/images/{project_id}")
async def get_images(project_id: str):
    """
    获取项目的图片列表
    """
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM images WHERE project_id = ?",
            (project_id,)
        )
        rows = await cursor.fetchall()
        
        if not rows:
            raise HTTPException(status_code=404, detail="项目不存在或没有图片")
        
        images = []
        for row in rows:
            preview_url = f"/uploads/{project_id}/{row['filename']}"
            images.append({
                "id": row["id"],
                "filename": row["filename"],
                "original_name": row["original_name"],
                "file_size": row["file_size"],
                "width": row["width"],
                "height": row["height"],
                "preview_url": preview_url
            })
        
        return {"project_id": project_id, "images": images}


@router.delete("/project/{project_id}")
async def delete_project(project_id: str):
    """
    删除项目及其所有文件
    """
    # 删除文件
    file_handler.delete_project_files(project_id)
    
    # 删除数据库记录
    async with get_db() as db:
        await db.execute("DELETE FROM issues WHERE detection_id IN (SELECT id FROM detection_results WHERE project_id = ?)", (project_id,))
        await db.execute("DELETE FROM detection_results WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM images WHERE project_id = ?", (project_id,))
        await db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        await db.commit()
    
    return {"message": "项目已删除"}

