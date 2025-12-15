"""
文件处理服务
"""
import os
import uuid
from PIL import Image
from typing import Optional, Tuple
import aiofiles


class FileHandler:
    """文件处理器"""
    
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.webp'}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    def __init__(self, upload_dir: str):
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)
    
    def is_allowed_file(self, filename: str) -> bool:
        """检查文件扩展名是否允许"""
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.ALLOWED_EXTENSIONS
    
    def generate_filename(self, original_name: str) -> str:
        """生成唯一文件名"""
        ext = os.path.splitext(original_name)[1].lower()
        return f"{uuid.uuid4().hex}{ext}"
    
    def get_project_dir(self, project_id: str) -> str:
        """获取项目目录"""
        project_dir = os.path.join(self.upload_dir, project_id)
        os.makedirs(project_dir, exist_ok=True)
        return project_dir
    
    async def save_file(self, file_content: bytes, project_id: str, original_name: str) -> dict:
        """
        保存上传的文件
        返回文件信息
        """
        # 检查文件类型
        if not self.is_allowed_file(original_name):
            raise ValueError(f"不支持的文件类型: {original_name}")
        
        # 检查文件大小
        if len(file_content) > self.MAX_FILE_SIZE:
            raise ValueError(f"文件过大: {original_name}")
        
        # 生成文件名和路径
        filename = self.generate_filename(original_name)
        project_dir = self.get_project_dir(project_id)
        file_path = os.path.join(project_dir, filename)
        
        # 保存文件
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        
        # 获取图片信息
        width, height = self.get_image_dimensions(file_path)
        
        return {
            "id": uuid.uuid4().hex,
            "filename": filename,
            "original_name": original_name,
            "file_path": file_path,
            "file_size": len(file_content),
            "width": width,
            "height": height,
            "preview_url": f"/uploads/{project_id}/{filename}"
        }
    
    def get_image_dimensions(self, file_path: str) -> Tuple[Optional[int], Optional[int]]:
        """获取图片尺寸"""
        try:
            with Image.open(file_path) as img:
                return img.size
        except Exception:
            return None, None
    
    def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False
    
    def delete_project_files(self, project_id: str) -> bool:
        """删除项目所有文件"""
        try:
            project_dir = os.path.join(self.upload_dir, project_id)
            if os.path.exists(project_dir):
                import shutil
                shutil.rmtree(project_dir)
                return True
            return False
        except Exception:
            return False

