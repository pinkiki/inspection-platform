"""
场景分析相关路由
"""
from fastapi import APIRouter, HTTPException

from services.mock_ai import mock_ai
from database import get_db

router = APIRouter()


@router.post("/scene/{project_id}")
async def analyze_scene(project_id: str):
    """
    分析项目图片的场景类型
    """
    # 获取项目图片数量
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT COUNT(*) as count FROM images WHERE project_id = ?",
            (project_id,)
        )
        row = await cursor.fetchone()
        
        if not row or row["count"] == 0:
            raise HTTPException(status_code=404, detail="项目不存在或没有图片")
        
        image_count = row["count"]
    
    # 模拟场景分析
    result = mock_ai.analyze_scene(image_count)
    
    # 更新项目的场景类型
    async with get_db() as db:
        await db.execute(
            "UPDATE projects SET scene_type = ?, status = ? WHERE id = ?",
            (result["primary_scene"]["id"], "analyzed", project_id)
        )
        await db.commit()
    
    return {
        "project_id": project_id,
        "image_count": image_count,
        "primary_scene": result["primary_scene"],
        "all_scenes": result["all_scenes"]
    }


@router.get("/algorithms/{scene_type}")
async def get_algorithms(scene_type: str):
    """
    获取指定场景类型的可用算法
    """
    # 查找场景定义
    scene = None
    for s in mock_ai.SCENE_TYPES:
        if s["id"] == scene_type:
            scene = s
            break
    
    if not scene:
        raise HTTPException(status_code=404, detail="场景类型不存在")
    
    return {
        "scene_type": scene_type,
        "scene_name": scene["name"],
        "algorithms": [
            {"id": f"algo-{i}", "name": algo, "description": f"{algo}算法"}
            for i, algo in enumerate(scene["algorithms"])
        ]
    }


@router.put("/scene/{project_id}")
async def update_scene(project_id: str, scene_type: str):
    """
    手动更新项目的场景类型
    """
    # 验证场景类型是否存在
    valid_scene = False
    for s in mock_ai.SCENE_TYPES:
        if s["id"] == scene_type:
            valid_scene = True
            break
    
    if not valid_scene:
        raise HTTPException(status_code=400, detail="无效的场景类型")
    
    # 更新数据库
    async with get_db() as db:
        cursor = await db.execute(
            "UPDATE projects SET scene_type = ? WHERE id = ?",
            (scene_type, project_id)
        )
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        await db.commit()
    
    return {"message": "场景类型已更新", "scene_type": scene_type}

