"""
额外资料上传相关路由
支持PoS信息、SfM结果、正射影像、三维模型等文件上传
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, BackgroundTasks
from typing import Optional, List
import uuid
import os
import shutil
from datetime import datetime

router = APIRouter(prefix="/api/supplementary", tags=["supplementary"])

# 上传目录
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
SUPPLEMENTARY_DIR = os.path.join(UPLOAD_DIR, "supplementary")

# 确保目录存在
os.makedirs(SUPPLEMENTARY_DIR, exist_ok=True)

# 支持的文件格式
ALLOWED_FORMATS = {
    'pos': ['.csv', '.txt', '.xml'],
    'sfm': ['.psx', '.psz', '.p4d', '.xml'],
    'ortho': ['.tif', '.tiff', '.jpg', '.jpeg', '.png'],
    'model3d': ['.obj', '.ply', '.fbx', '.glb', '.gltf', '.b3dm', '.3mx', '.osgb']
}

# 数据来源软件
DATA_SOURCES = {
    'dji_terra': {
        'name': '大疆智图',
        'formats': {
            'pos': ['.csv', '.txt'],
            'sfm': [],
            'ortho': ['.tif'],
            'model3d': ['.obj', '.b3dm']
        }
    },
    'metashape': {
        'name': 'Metashape',
        'formats': {
            'pos': ['.csv', '.xml'],
            'sfm': ['.psx', '.psz'],
            'ortho': ['.tif'],
            'model3d': ['.obj', '.ply']
        }
    },
    'pix4d': {
        'name': 'Pix4D',
        'formats': {
            'pos': ['.csv'],
            'sfm': ['.p4d'],
            'ortho': ['.tif'],
            'model3d': ['.obj', '.ply']
        }
    },
    'context_capture': {
        'name': 'Context Capture',
        'formats': {
            'pos': ['.csv'],
            'sfm': ['.xml'],
            'ortho': ['.tif'],
            'model3d': ['.obj', '.3mx', '.osgb']
        }
    },
    'other': {
        'name': '其他/自定义',
        'formats': {
            'pos': ['.csv', '.txt', '.xml'],
            'sfm': [],
            'ortho': ['.tif', '.tiff', '.jpg', '.png'],
            'model3d': ['.obj', '.ply', '.fbx', '.glb', '.gltf']
        }
    }
}

# 积分折扣配置
DISCOUNT_CONFIG = {
    'pos': {'discount': 10, 'time_saved': '10-15分钟'},
    'sfm': {'discount': 30, 'time_saved': '30-60分钟'},
    'ortho': {'discount': 50, 'time_saved': '跳过正射生成'},
    'model3d': {'discount': 50, 'time_saved': '跳过模型重建'}
}

# 内存存储（实际应使用数据库）
uploads_store = {}


def is_allowed_file(filename: str, file_type: str, data_source: str = 'other') -> bool:
    """检查文件是否为允许的格式"""
    ext = os.path.splitext(filename)[1].lower()
    
    # 优先使用数据来源的格式限制
    if data_source in DATA_SOURCES:
        allowed = DATA_SOURCES[data_source]['formats'].get(file_type, [])
        if allowed:
            return ext in allowed
    
    # 回退到通用格式
    return ext in ALLOWED_FORMATS.get(file_type, [])


async def save_file_async(file: UploadFile, project_id: str, file_type: str) -> dict:
    """异步保存文件"""
    # 创建项目目录
    project_dir = os.path.join(SUPPLEMENTARY_DIR, project_id)
    os.makedirs(project_dir, exist_ok=True)
    
    # 生成唯一文件名
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1].lower()
    new_filename = f"{file_type}_{file_id}{ext}"
    file_path = os.path.join(project_dir, new_filename)
    
    # 保存文件
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    file_size = os.path.getsize(file_path)
    
    return {
        "id": file_id,
        "type": file_type,
        "original_name": file.filename,
        "filename": new_filename,
        "file_path": file_path,
        "file_size": file_size,
        "uploaded_at": datetime.now().isoformat()
    }


@router.get("/sources")
async def get_data_sources():
    """获取支持的数据来源软件列表"""
    return {
        "sources": [
            {
                "id": key,
                "name": value['name'],
                "formats": value['formats']
            }
            for key, value in DATA_SOURCES.items()
        ]
    }


@router.get("/discounts")
async def get_discount_config():
    """获取积分折扣配置"""
    return {
        "discounts": DISCOUNT_CONFIG,
        "max_discount": 70
    }


@router.post("/upload")
async def upload_supplementary_file(
    file: UploadFile = File(...),
    project_id: str = Form(...),
    file_type: str = Form(...),
    data_source: str = Form(default='other')
):
    """
    上传额外资料文件
    
    Parameters:
    - file: 上传的文件
    - project_id: 项目ID
    - file_type: 文件类型 (pos, sfm, ortho, model3d)
    - data_source: 数据来源软件
    """
    # 验证文件类型
    if file_type not in ALLOWED_FORMATS:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file_type}")
    
    # 验证文件格式
    if not is_allowed_file(file.filename, file_type, data_source):
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的文件格式。{file_type} 类型支持的格式: {', '.join(ALLOWED_FORMATS[file_type])}"
        )
    
    try:
        # 保存文件
        file_info = await save_file_async(file, project_id, file_type)
        
        # 存储上传记录
        if project_id not in uploads_store:
            uploads_store[project_id] = {
                "data_source": data_source,
                "files": []
            }
        
        uploads_store[project_id]["files"].append(file_info)
        
        # 计算折扣
        discount = DISCOUNT_CONFIG.get(file_type, {}).get('discount', 0)
        
        return {
            "success": True,
            "file": file_info,
            "discount": discount,
            "message": f"文件上传成功，可节省 {discount}% 积分"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.post("/upload-batch")
async def upload_supplementary_files_batch(
    files: List[UploadFile] = File(...),
    project_id: str = Form(...),
    file_types: str = Form(...),  # 逗号分隔的类型列表
    data_source: str = Form(default='other')
):
    """
    批量上传额外资料文件
    
    Parameters:
    - files: 上传的文件列表
    - project_id: 项目ID
    - file_types: 文件类型列表，逗号分隔 (如 "pos,sfm,ortho")
    - data_source: 数据来源软件
    """
    types_list = file_types.split(',')
    
    if len(files) != len(types_list):
        raise HTTPException(
            status_code=400, 
            detail="文件数量与类型数量不匹配"
        )
    
    uploaded_files = []
    total_discount = 0
    
    for file, file_type in zip(files, types_list):
        file_type = file_type.strip()
        
        # 验证文件类型
        if file_type not in ALLOWED_FORMATS:
            continue
        
        # 验证文件格式
        if not is_allowed_file(file.filename, file_type, data_source):
            continue
        
        try:
            file_info = await save_file_async(file, project_id, file_type)
            uploaded_files.append(file_info)
            total_discount += DISCOUNT_CONFIG.get(file_type, {}).get('discount', 0)
        except Exception:
            continue
    
    if not uploaded_files:
        raise HTTPException(status_code=400, detail="没有有效的文件被上传")
    
    # 存储上传记录
    if project_id not in uploads_store:
        uploads_store[project_id] = {
            "data_source": data_source,
            "files": []
        }
    
    uploads_store[project_id]["files"].extend(uploaded_files)
    
    # 限制最大折扣
    total_discount = min(total_discount, 70)
    
    return {
        "success": True,
        "files": uploaded_files,
        "total_discount": total_discount,
        "message": f"成功上传 {len(uploaded_files)} 个文件，可节省 {total_discount}% 积分"
    }


@router.get("/project/{project_id}")
async def get_project_supplementary(project_id: str):
    """获取项目的额外资料"""
    if project_id not in uploads_store:
        return {
            "project_id": project_id,
            "data_source": None,
            "files": [],
            "total_discount": 0
        }
    
    project_data = uploads_store[project_id]
    files = project_data.get("files", [])
    
    # 计算总折扣
    total_discount = 0
    for file_info in files:
        file_type = file_info.get("type")
        total_discount += DISCOUNT_CONFIG.get(file_type, {}).get('discount', 0)
    
    total_discount = min(total_discount, 70)
    
    return {
        "project_id": project_id,
        "data_source": project_data.get("data_source"),
        "files": files,
        "total_discount": total_discount
    }


@router.delete("/project/{project_id}")
async def delete_project_supplementary(project_id: str):
    """删除项目的额外资料"""
    # 删除文件
    project_dir = os.path.join(SUPPLEMENTARY_DIR, project_id)
    if os.path.exists(project_dir):
        shutil.rmtree(project_dir)
    
    # 删除记录
    if project_id in uploads_store:
        del uploads_store[project_id]
    
    return {"success": True, "message": "额外资料已删除"}


@router.delete("/file/{project_id}/{file_id}")
async def delete_supplementary_file(project_id: str, file_id: str):
    """删除单个额外资料文件"""
    if project_id not in uploads_store:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    files = uploads_store[project_id].get("files", [])
    file_to_delete = None
    
    for i, file_info in enumerate(files):
        if file_info["id"] == file_id:
            file_to_delete = file_info
            files.pop(i)
            break
    
    if not file_to_delete:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 删除物理文件
    if os.path.exists(file_to_delete["file_path"]):
        os.remove(file_to_delete["file_path"])
    
    return {"success": True, "message": "文件已删除"}

