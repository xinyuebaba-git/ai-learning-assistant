# Course AI Helper - 快速开始指南

## 🚀 一键启动（推荐）

### 首次运行

```bash
# 1. 克隆项目
git clone https://github.com/xinyuebaba-git/ai-learning-assistant.git
cd ai-learning-assistant

# 2. 赋予执行权限
chmod +x start-dev.sh stop-dev.sh

# 3. 安装 Redis（如果未安装）
# macOS
brew install redis

# Ubuntu/Debian
sudo apt install redis-server

# 4. 一键启动
./start-dev.sh
```

### 日常使用

```bash
# 启动所有服务
./start-dev.sh

# 停止所有服务
./stop-dev.sh

# 查看日志
tail -f backend/logs/backend.log
tail -f logs/frontend.log
tail -f backend/logs/celery_worker.log
```

## 📱 访问地址

启动成功后，访问以下地址：

- **前端界面**: http://localhost:3000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 🔧 手动启动（备选）

如果一键启动脚本失败，可以手动启动：

### 1. 启动 Redis

```bash
# macOS
brew services start redis

# Ubuntu/Debian
sudo systemctl start redis-server
```

### 2. 安装依赖

```bash
# 后端
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 前端
cd ../frontend
npm install
```

### 3. 启动 Celery Worker

```bash
cd backend
source .venv/bin/activate
celery -A app.core.celery_app worker \
    --loglevel=info \
    --queues=video_processing,asr,llm \
    --concurrency=4
```

### 4. 启动 FastAPI 后端（新终端）

```bash
cd backend
source .venv/bin/activate
python3 main.py
```

### 5. 启动前端（新终端）

```bash
cd frontend
npm run dev
```

## 🧪 测试验证

### 1. 检查服务状态

```bash
# 检查 Redis
redis-cli ping
# 应输出：PONG

# 检查后端
curl http://localhost:8000/health
# 应输出：{"status":"healthy"}

# 检查前端
curl http://localhost:3000
# 应返回 HTML
```

### 2. 测试视频处理

```bash
# 1. 登录获取 token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}'

# 2. 扫描视频
curl -X POST http://localhost:8000/api/videos/scan \
  -H "Authorization: Bearer <token>"

# 3. 处理视频（异步）
curl -X POST http://localhost:8000/api/videos/1/process \
  -H "Authorization: Bearer <token>"

# 4. 查询进度
curl http://localhost:8000/api/videos/1/process/status \
  -H "Authorization: Bearer <token>"
```

## 🐛 故障排查

### 问题 1: Redis 连接失败

```bash
# 检查 Redis 是否运行
redis-cli ping

# 重启 Redis
brew services restart redis  # macOS
sudo systemctl restart redis-server  # Linux
```

### 问题 2: 端口被占用

```bash
# 查看端口占用
lsof -ti:8000 | xargs kill -9  # 后端端口
lsof -ti:3000 | xargs kill -9  # 前端端口
```

### 问题 3: Celery Worker 不工作

```bash
# 查看 Worker 日志
tail -f backend/logs/celery_worker.log

# 重启 Worker
./stop-dev.sh
./start-dev.sh
```

### 问题 4: 前端无法访问

```bash
# 查看前端日志
tail -f logs/frontend.log

# 检查 Vite 配置
cat frontend/vite.config.ts
```

## 📊 监控 Celery 任务

### 查看 Worker 状态

```bash
cd backend
source .venv/bin/activate

# 查看活跃任务
celery -A app.core.celery_app inspect active

# 查看注册任务
celery -A app.core.celery_app inspect registered

# 查看 Worker 统计
celery -A app.core.celery_app inspect stats
```

### Flower 监控（可选）

```bash
# 安装 Flower
pip install flower

# 启动 Flower
celery -A app.core.celery_app flower --port=5555

# 访问 http://localhost:5555
```

## 📁 目录结构

```
ai-learning-assistant/
├── start-dev.sh          # 一键启动脚本
├── stop-dev.sh           # 一键停止脚本
├── QUICKSTART.md         # 本文件
├── backend/
│   ├── app/
│   │   ├── api/         # API 路由
│   │   ├── core/        # 核心配置（含 Celery）
│   │   ├── tasks/       # Celery 任务
│   │   └── services/    # 业务服务
│   ├── logs/            # 日志目录
│   └── main.py          # 后端入口
└── frontend/
    ├── src/             # 前端源码
    ├── logs/            # 日志目录
    └── package.json     # Node 依赖
```

## 🔗 相关文档

- [Celery 配置指南](backend/CELERY_SETUP.md)
- [项目 README](README.md)
- [部署指南](DEPLOY.md)

---

*更新时间：2026-03-03*  
*维护者：公司小龙虾 🦞*
