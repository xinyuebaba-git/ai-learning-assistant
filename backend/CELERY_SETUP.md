# Celery 异步任务队列配置指南

## 📋 概述

本项目使用 **Celery + Redis** 实现异步任务处理，主要用于：
- 视频处理（生成字幕、总结、向量索引）
- ASR 语音识别
- LLM 内容生成

## 🏗️ 架构

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  FastAPI │────▶│  Celery  │────▶│  Redis   │
│   API    │     │  Worker  │     │  Broker  │
└──────────┘     └──────────┘     └──────────┘
                      │
                      ▼
               ┌──────────┐
               │  Tasks   │
               │ - Video  │
               │ - ASR    │
               │ - LLM    │
               └──────────┘
```

## 🚀 快速开始

### 1. 安装 Redis

**macOS:**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
```

**验证 Redis:**
```bash
redis-cli ping
# 应输出：PONG
```

### 2. 启动 Celery Worker

```bash
cd backend
source .venv/bin/activate

# 方式 1: 使用启动脚本
./start_celery_worker.sh

# 方式 2: 手动启动
celery -A app.core.celery_app worker \
    --loglevel=info \
    --queues=video_processing,asr,llm \
    --concurrency=4
```

### 3. 启动 FastAPI 后端

```bash
# 新终端
python3 main.py
```

## 📝 使用示例

### 提交视频处理任务

```python
from app.tasks.video_tasks import process_video_task

# 异步提交任务
task = process_video_task.delay(video_id=1)

# 获取任务 ID
print(f"Task ID: {task.id}")
```

### 查询任务进度

```python
from app.tasks.video_tasks import get_task_progress
from celery.result import AsyncResult

# 方式 1: 使用任务函数
result = get_task_progress.delay(task_id)

# 方式 2: 使用 AsyncResult
task_result = AsyncResult(task_id, app=celery_app)
print(f"Status: {task_result.status}")
```

### API 调用

```bash
# 1. 提交处理任务
curl -X POST http://localhost:8000/api/videos/1/process \
  -H "Authorization: Bearer <token>"

# 响应:
# {
#   "task_id": "abc123...",
#   "status": "queued",
#   "check_status_url": "/api/videos/1/process/status"
# }

# 2. 查询进度
curl http://localhost:8000/api/videos/1/process/status?task_id=abc123 \
  -H "Authorization: Bearer <token>"
```

## 🔧 配置说明

### Celery 配置 (app/core/celery_app.py)

```python
celery_app = Celery(
    'course_ai',
    broker='redis://localhost:6379/0',  # Broker
    backend='redis://localhost:6379/1', # Backend
)
```

### 任务队列

| 队列名 | 用途 | 优先级 |
|--------|------|--------|
| `video_processing` | 视频处理 | 中 |
| `asr` | ASR 语音识别 | 高 |
| `llm` | LLM 内容生成 | 中 |

### Worker 配置

```bash
# 并发数：4
--concurrency=4

# 监听队列
--queues=video_processing,asr,llm

# 日志级别
--loglevel=info
```

## 📊 监控

### 查看 Worker 状态

```bash
# 查看活跃 Worker
celery -A app.core.celery_app inspect active

# 查看注册的任务
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

## 🐛 故障排查

### 问题 1: Redis 连接失败

```bash
# 检查 Redis 是否运行
redis-cli ping

# 重启 Redis
brew services restart redis  # macOS
sudo systemctl restart redis-server  # Linux
```

### 问题 2: 任务不执行

1. **检查 Worker 是否运行**
   ```bash
   ps aux | grep celery
   ```

2. **检查队列名称**
   ```bash
   celery -A app.core.celery_app inspect active
   ```

3. **查看 Worker 日志**
   ```bash
   # Worker 启动时会有详细日志
   ```

### 问题 3: 任务卡住

```bash
# 查看任务状态
celery -A app.core.celery_app inspect active

# 重启 Worker
# Ctrl+C 停止，然后重新启动
```

## 📈 性能优化

### 1. 调整并发数

根据 CPU 核心数调整：
```bash
# 4 核 CPU
--concurrency=4

# 8 核 CPU
--concurrency=8
```

### 2. 使用 Gevent 池

```bash
# 安装 gevent
pip install gevent

# 启动 Worker
celery -A app.core.celery_app worker \
    --pool=gevent \
    --concurrency=100
```

### 3. 任务路由

```python
# 在 celery_app.py 中配置
task_routes = {
    'app.tasks.video_tasks.process_video_task': {
        'queue': 'video_processing'
    },
}
```

## 🔒 安全建议

1. **Redis 认证**
   ```python
   broker='redis://:password@localhost:6379/0'
   ```

2. **限制任务序列化**
   ```python
   accept_content=['json']
   task_serializer='json'
   ```

3. **设置任务过期时间**
   ```python
   result_expires=3600  # 1 小时
   ```

## 📚 参考资料

- [Celery 官方文档](https://docs.celeryq.dev/)
- [Redis 官方文档](https://redis.io/documentation)
- [Celery 最佳实践](https://docs.celeryq.dev/en/stable/userguide/best-practices.html)

---

*创建时间：2026-03-03*  
*维护者：公司小龙虾 🦞*
