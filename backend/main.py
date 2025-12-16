"""
智巡 - AI无人机巡检平台 后端服务
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from routes import upload, analysis, report, export, credits, advanced, supplementary, user_db as user
from api import step_snapshots

# 创建FastAPI应用
app = FastAPI(
    title="智巡 AI巡检平台",
    description="基于AI的无人机巡检图像处理平台",
    version="0.1.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 确保uploads目录存在
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 静态文件服务
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# 注册路由
app.include_router(upload.router, prefix="/api/upload", tags=["上传"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["场景分析"])
app.include_router(report.router, prefix="/api/report", tags=["报告"])
app.include_router(export.router, prefix="/api/export", tags=["导出"])
app.include_router(credits.router, tags=["积分"])
app.include_router(advanced.router, tags=["进阶处理"])
app.include_router(supplementary.router, tags=["额外资料"])
app.include_router(user.router, tags=["用户"])
app.include_router(step_snapshots.router)


@app.get("/")
async def root():
    return {"message": "智巡 AI巡检平台 API", "version": "0.1.0"}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

