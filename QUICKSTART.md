# Course AI Helper - 快速开始指南

## 5 分钟快速体验

### 1. 克隆项目

```bash
cd /Users/nannan/.openclaw/workspace
# 项目已创建完成
```

### 2. 启动服务

```bash
cd course-ai-helper

# 方式 A: 使用启动脚本（推荐）
./start.sh

# 方式 B: 使用 Docker
docker-compose up -d
```

### 3. 访问系统

打开浏览器访问：
- **前端**: http://localhost:3000
- **API 文档**: http://localhost:8000/docs

### 4. 注册账号

1. 点击"立即注册"
2. 输入邮箱、用户名、密码
3. 完成注册

### 5. 添加视频

#### 方法 1: 扫描本地目录

```bash
# 将视频文件放入 data/videos 目录
cp /path/to/your/video.mp4 data/videos/

# 在网页中点击"扫描新视频"
```

#### 方法 2: API 上传

```bash
curl -X POST http://localhost:8000/api/videos/scan \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 6. 处理视频

1. 在视频列表中点击视频
2. 点击"开始处理"按钮
3. 等待处理完成（ASR + 总结）

### 7. 搜索内容

1. 点击顶部"搜索"菜单
2. 输入关键词（如"人工智能"）
3. 查看搜索结果，点击跳转到对应时间点

---

## 配置 LLM

### 使用本地 Ollama（免费）

```bash
# 安装 Ollama
# macOS
brew install ollama

# 启动 Ollama
ollama serve

# 拉取模型
ollama pull qwen2.5:7b

# 编辑 .env
DEFAULT_LLM_BACKEND=local
OLLAMA_MODEL=qwen2.5:7b
```

### 使用 DeepSeek（云端 API）

```bash
# 获取 API Key: https://platform.deepseek.com/

# 编辑 .env
DEFAULT_LLM_BACKEND=deepseek
DEEPSEEK_API_KEY=sk-your-api-key
DEEPSEEK_MODEL=deepseek-chat
```

### 使用 OpenAI（云端 API）

```bash
# 获取 API Key: https://platform.openai.com/

# 编辑 .env
DEFAULT_LLM_BACKEND=openai
OPENAI_API_KEY=sk-your-api-key
OPENAI_MODEL=gpt-4.1-mini
```

---

## 常用操作

### 查看处理进度

```bash
# 查看后端日志
docker logs course-ai-backend -f

# 或查看本地日志
tail -f backend/logs/*.log
```

### 备份数据

```bash
# 备份整个 data 目录
tar -czf course-ai-backup-$(date +%Y%m%d).tar.gz data/
```

### 重置系统

```bash
# 删除所有数据
rm -rf data/*

# 重启服务
docker-compose down
docker-compose up -d
```

---

## 下一步

- 📖 阅读 [DEPLOY.md](./DEPLOY.md) 了解详细部署选项
- 🔧 查看 [API 文档](http://localhost:8000/docs) 了解完整 API
- 💬 遇到问题？查看故障排查章节

---

## 系统要求

| 组件 | 最低要求 | 推荐配置 |
|------|----------|----------|
| CPU | 4 核 | 8 核+ |
| 内存 | 8GB | 16GB+ |
| 存储 | 10GB | 50GB+ |
| GPU | 可选 | NVIDIA 8GB+ (加速 ASR/LLM) |

---

祝你使用愉快！🎓🦞
