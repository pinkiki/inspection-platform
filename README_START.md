# 启动说明

## 固定端口配置

为了确保端口一致性，已将服务固定在以下端口：

- **后端服务**：`http://localhost:8000`
- **前端服务**：`http://localhost:5173`

## 启动方式

### 方法1：使用启动脚本（推荐）

```bash
# 启动后端
cd /Users/monica/Desktop/inspection-platform/backend
./start.sh

# 在另一个终端启动前端
cd /Users/monica/Desktop/inspection-platform/frontend
./start.sh
```

### 方法2：手动启动

```bash
# 启动后端（固定8000端口）
cd /Users/monica/Desktop/inspection-platform/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 启动前端（固定5173端口）
cd /Users/monica/Desktop/inspection-platform/frontend
npm run dev
```

## 重要说明

1. 如果遇到端口被占用的错误，请先停止占用端口的进程：
   ```bash
   # 查看8000端口的进程
   lsof -i :8000
   # 查看前端5173端口的进程
   lsof -i :5173
   ```

2. 前端配置了 `strictPort: true`，如果5173端口被占用会直接报错，而不是自动切换到其他端口

3. 前端的API代理配置已设置为指向 `http://localhost:8000`