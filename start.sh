#!/bin/bash
# 智巡平台启动脚本 (Linux/macOS)

echo "========================================"
echo "  智巡 - AI无人机巡检平台"
echo "========================================"
echo ""

cd "$(dirname "$0")"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3"
    exit 1
fi

# 运行启动脚本
python3 run.py

