# 🚀 Course AI Helper - 启动指南

## 一键启动（推荐）

### 方式 1: 交互式菜单

```bash
./start-all.sh
```

然后选择操作：
- `1)` 启动所有服务（后端 + 前端）
- `2)` 仅启动后端
- `3)` 仅启动前端
- `4)` 停止所有服务
- `5)` 查看服务状态
- `6)` 查看日志
- `7)` 重启所有服务
- `0)` 退出

### 方式 2: 命令行参数

```bash
# 启动所有服务
./start-all.sh start

# 停止所有服务
./start-all.sh stop

# 重启所有服务
./start-all.sh restart

# 查看服务状态
./start-all.sh status

# 查看日志
./start-all.sh logs
```

---

## 快速启动（后台模式）

### 启动后端

```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
```

### 启动前端

```bash
cd frontend
npm run dev &
```

---

## Docker 启动（生产环境）

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

---

## 访问地址

启动成功后，访问以下地址：

| 服务 | 地址 | 说明 |
|------|------|------|
| **前端界面** | http://localhost:3000 | 用户界面 |
| **后端 API** | http://localhost:8000 | API 服务 |
| **API 文档** | http://localhost:8000/docs | Swagger 文档 |
| **健康检查** | http://localhost:8000/health | 健康状态 |

---

## 常见问题

### Q: 端口被占用怎么办？

```bash
# 清理 8000 端口
lsof -ti:8000 | xargs kill -9

# 或使用启动脚本自动清理
./start-all.sh restart
```

### Q: 如何查看日志？

```bash
# 使用脚本查看
./start-all.sh logs

# 或直接查看日志文件
tail -f logs/backend.log
tail -f logs/frontend.log
```

### Q: 如何停止服务？

```bash
# 使用脚本停止
./start-all.sh stop

# 或手动停止
pkill -f "uvicorn main:app"
pkill -f "vite"
```

### Q: 首次启动需要做什么？

```bash
# 1. 安装后端依赖
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. 安装前端依赖
cd frontend
npm install

# 3. 启动服务
cd ..
./start-all.sh start
```

---

## 环境变量配置

启动前，建议配置环境变量：

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置
vi .env

# 重要配置项：
# - SECRET_KEY: JWT 密钥（生产环境务必修改）
# - DEEPSEEK_API_KEY: DeepSeek API Key（如使用云端）
# - OPENAI_API_KEY: OpenAI API Key（如使用云端）
# - DEFAULT_LLM_BACKEND: 后端类型（local/deepseek/openai）
```

---

## 服务检查

启动后，检查服务是否正常：

```bash
# 检查后端
curl http://localhost:8000/health
# 应返回：{"status": "healthy"}

# 检查前端
curl http://localhost:3000
# 应返回 HTML 内容

# 检查 API 文档
open http://localhost:8000/docs
```

---

## 日志位置

```
logs/
├── backend.log    # 后端日志
└── frontend.log   # 前端日志
```

---

**祝你使用愉快！** 🦞
