#!/bin/bash

# 启动后端服务的脚本，固定使用8000端口

echo "Starting backend server on port 8000..."
cd /Users/monica/Desktop/inspection-platform/backend

# 使用python直接运行，默认使用FastAPI的8000端口
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 或者使用：uvicorn main:app --reload --port 8000