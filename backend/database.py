"""
数据库配置和连接
"""
import aiosqlite
import os
from contextlib import asynccontextmanager

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "inspection.db")


async def init_db():
    """初始化数据库表"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # 项目表
        await db.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT,
                location TEXT,
                inspection_date TEXT,
                inspector TEXT,
                company TEXT,
                scene_type TEXT,
                template_id TEXT,
                status TEXT DEFAULT 'uploading',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 图片表
        await db.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                filename TEXT,
                original_name TEXT,
                file_path TEXT,
                file_size INTEGER,
                width INTEGER,
                height INTEGER,
                gps_lat REAL,
                gps_lng REAL,
                captured_at TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)
        
        # 检测结果表
        await db.execute("""
            CREATE TABLE IF NOT EXISTS detection_results (
                id TEXT PRIMARY KEY,
                image_id TEXT,
                project_id TEXT,
                confidence REAL,
                status TEXT,
                suggestion TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (image_id) REFERENCES images(id),
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)
        
        # 问题/缺陷表
        await db.execute("""
            CREATE TABLE IF NOT EXISTS issues (
                id TEXT PRIMARY KEY,
                detection_id TEXT,
                issue_type TEXT,
                name TEXT,
                severity TEXT,
                description TEXT,
                confidence REAL,
                bbox_x REAL,
                bbox_y REAL,
                bbox_width REAL,
                bbox_height REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (detection_id) REFERENCES detection_results(id)
            )
        """)
        
        await db.commit()


@asynccontextmanager
async def get_db():
    """获取数据库连接"""
    db = await aiosqlite.connect(DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()

