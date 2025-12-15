#!/usr/bin/env python3
"""
智巡平台启动脚本
同时启动后端API服务和前端开发服务器
"""
import subprocess
import sys
import os
import time
import signal
import platform

# 项目根目录
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

# 端口配置
BACKEND_PORT = 8000
FRONTEND_PORT = 5173

processes = []


def signal_handler(sig, frame):
    """处理Ctrl+C信号"""
    print("\n正在停止服务...")
    for p in processes:
        try:
            p.terminate()
        except:
            pass
    sys.exit(0)


def kill_port(port):
    """释放占用指定端口的进程"""
    system = platform.system()
    
    try:
        if system == "Darwin" or system == "Linux":
            # macOS / Linux
            result = subprocess.run(
                f"lsof -ti:{port}",
                shell=True,
                capture_output=True,
                text=True
            )
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        subprocess.run(f"kill -9 {pid}", shell=True, capture_output=True)
                print(f"✓ 已释放端口 {port} (PID: {', '.join(pids)})")
                return True
        elif system == "Windows":
            # Windows
            result = subprocess.run(
                f"netstat -ano | findstr :{port}",
                shell=True,
                capture_output=True,
                text=True
            )
            if result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                pids = set()
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 5:
                        pids.add(parts[-1])
                for pid in pids:
                    if pid and pid != '0':
                        subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
                print(f"✓ 已释放端口 {port}")
                return True
    except Exception as e:
        print(f"释放端口 {port} 时出错: {e}")
    
    return False


def release_ports():
    """释放后端和前端端口"""
    print("检查端口占用...")
    backend_released = kill_port(BACKEND_PORT)
    frontend_released = kill_port(FRONTEND_PORT)
    
    if not backend_released and not frontend_released:
        print("✓ 端口未被占用")
    
    # 等待端口完全释放
    time.sleep(0.5)


def check_node():
    """检查Node.js是否安装"""
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Node.js 版本: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    print("✗ 未找到 Node.js，请先安装 Node.js 18+")
    return False


def check_python_packages():
    """检查Python包是否安装"""
    required = ["fastapi", "uvicorn", "aiosqlite", "pillow"]
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print(f"缺少Python包: {', '.join(missing)}")
        print("正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", 
                       os.path.join(ROOT_DIR, "requirements.txt")])
    else:
        print("✓ Python依赖已就绪")


def install_frontend_deps():
    """安装前端依赖"""
    node_modules = os.path.join(FRONTEND_DIR, "node_modules")
    if not os.path.exists(node_modules):
        print("正在安装前端依赖...")
        system = platform.system()
        if system == "Windows":
            subprocess.run("npm install", cwd=FRONTEND_DIR, shell=True)
        else:
            subprocess.run(["npm", "install"], cwd=FRONTEND_DIR, shell=False)
    else:
        print("✓ 前端依赖已就绪")


def init_database():
    """初始化数据库"""
    print("初始化数据库...")
    sys.path.insert(0, BACKEND_DIR)
    import asyncio
    from database import init_db
    asyncio.run(init_db())
    print("✓ 数据库已就绪")


def start_backend():
    """启动后端服务"""
    print("\n启动后端服务 (http://localhost:8000)...")
    env = os.environ.copy()
    env["PYTHONPATH"] = BACKEND_DIR
    
    p = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
        cwd=BACKEND_DIR,
        env=env
    )
    processes.append(p)
    return p


def start_frontend():
    """启动前端开发服务器"""
    print("启动前端服务 (http://localhost:5173)...")
    
    system = platform.system()
    
    if system == "Windows":
        # Windows 使用 shell=True
        p = subprocess.Popen(
            "npm run dev",
            cwd=FRONTEND_DIR,
            shell=True
        )
    else:
        # macOS / Linux 不使用 shell
        p = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=FRONTEND_DIR,
            shell=False
        )
    
    processes.append(p)
    return p


def main():
    print("=" * 50)
    print("  智巡 - AI无人机巡检平台")
    print("=" * 50)
    print()
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 检查环境
    print("检查环境...")
    if not check_node():
        print("\n请安装 Node.js 后重试")
        print("下载地址: https://nodejs.org/")
        return
    
    check_python_packages()
    install_frontend_deps()
    init_database()
    
    # 释放端口
    release_ports()
    
    # 启动服务
    print("\n" + "=" * 50)
    backend_process = start_backend()
    time.sleep(2)  # 等待后端启动
    frontend_process = start_frontend()
    
    print("\n" + "=" * 50)
    print("服务已启动!")
    print("  - 前端地址: http://localhost:5173")
    print("  - 后端API: http://localhost:8000")
    print("  - API文档: http://localhost:8000/docs")
    print("\n按 Ctrl+C 停止所有服务")
    print("=" * 50)
    
    # 等待进程
    try:
        while True:
            time.sleep(1)
            # 检查进程是否还在运行
            if backend_process.poll() is not None:
                print("后端服务已停止")
                break
            if frontend_process.poll() is not None:
                print("前端服务已停止")
                break
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    main()

