# Course AI Helper - 部署指南

## 方式一：Docker Compose 部署（推荐）

### 1. 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 8GB 内存（使用本地 LLM 时建议 16GB+）

### 2. 配置环境变量

```bash
# 复制环境变量文件
cp .env.example .env

# 编辑 .env 文件
# - 设置 SECRET_KEY（生产环境务必修改）
# - 配置 LLM API Key（如使用云端 API）
```

### 3. 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 4. 访问服务

- **前端界面**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **Ollama**: http://localhost:11434

### 5. 初始化 Ollama 模型

```bash
# 如果使用本地 LLM，需要拉取模型
docker exec -it course-ai-ollama ollama pull qwen2.5:7b
```

---

## 方式二：本地开发部署

### 1. 后端部署

```bash
cd backend

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp ../.env.example .env
# 编辑 .env 文件

# 启动服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 前端部署

```bash
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 生产构建
npm run build
```

### 3. 快速启动脚本

```bash
# 使用启动脚本（自动完成所有步骤）
./start.sh
```

---

## 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `SECRET_KEY` | JWT 密钥 | 必须修改 |
| `DEFAULT_LLM_BACKEND` | LLM 后端 | `local` |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | - |
| `OPENAI_API_KEY` | OpenAI API Key | - |
| `OLLAMA_BASE_URL` | Ollama 地址 | `http://localhost:11434` |
| `ASR_ENGINE` | ASR 引擎 | `faster-whisper` |
| `ASR_MODEL` | ASR 模型 | `medium` |

### 目录结构

```
data/
├── videos/          # 视频文件（可挂载外部目录）
├── subtitles/       # 生成的字幕文件
├── summaries/       # 生成的总结文件
├── embeddings/      # 向量索引
└── chroma/          # ChromaDB 数据
```

---

## 生产环境建议

### 1. 数据库

使用 PostgreSQL 替代 SQLite：

```yaml
# docker-compose.yml 取消注释 postgres 服务
# 修改 DATABASE_URL
DATABASE_URL=postgresql+psycopg2://user:pass@postgres:5432/course_ai
```

### 2. GPU 加速

启用 GPU 加速 ASR 和 LLM：

```yaml
# docker-compose.yml 中 ollama 服务
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

### 3. 反向代理

使用 Nginx 反向代理：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:3000;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
    }
}
```

### 4. HTTPS

使用 Let's Encrypt 配置 SSL 证书。

---

## 故障排查

### Ollama 连接失败

```bash
# 检查 Ollama 服务
docker ps | grep ollama

# 查看 Ollama 日志
docker logs course-ai-ollama

# 测试连接
curl http://localhost:11434/api/tags
```

### 向量搜索失败

```bash
# 检查 ChromaDB 目录权限
ls -la data/chroma

# 重新创建向量索引
# 删除 data/chroma 目录后重启服务
```

### 视频处理失败

```bash
# 检查 ffmpeg 是否安装
ffmpeg -version

# 查看后端日志
docker logs course-ai-backend
```

---

## 更新升级

```bash
# 拉取最新代码
git pull

# 重新构建并重启
docker-compose down
docker-compose build
docker-compose up -d
```
