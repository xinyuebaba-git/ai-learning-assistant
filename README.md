# Course AI Helper - AI 课程学习辅助系统

基于 subgen 核心能力的视频课程学习辅助平台，支持多用户、语义搜索和知识点智能标记。

## ✨ 核心功能

1. **视频资源管理** - 检索、播放、收藏
2. **自动字幕生成** - 检测无字幕视频，自动调用 ASR 识别
3. **内容总结** - 大模型生成课程总结 + 知识点时间戳标记
4. **语义搜索** - 自然语言检索视频内容（字幕 + 总结）
5. **多用户支持** - 个人收藏、笔记、学习进度

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend (React)                    │
│   视频播放器 | 搜索界面 | 收藏管理 | 笔记系统            │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ 视频管理  │  │ ASR 服务  │  │ LLM 服务  │  │ 向量搜索  │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │ 用户认证  │  │ 数据库   │  │ 任务队列  │               │
│  └──────────┘  └──────────┘  └──────────┘               │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                     Data Layer                           │
│  PostgreSQL | ChromaDB | 视频文件 | 字幕文件 | 总结文件   │
└─────────────────────────────────────────────────────────┘
```

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.11 + FastAPI |
| 前端 | React 18 + TypeScript + Vite |
| 数据库 | PostgreSQL (用户/元数据) + ChromaDB (向量) |
| ASR | subgen 核心 (Whisper / Faster-Whisper) |
| LLM | Ollama (本地) / DeepSeek / OpenAI |
| 向量模型 | bge-small-zh-v1.5 |
| 部署 | Docker + Docker Compose |

## 📁 项目结构

```
course-ai-helper/
├── backend/
│   ├── app/
│   │   ├── api/           # API 路由
│   │   ├── core/          # 配置、安全、工具
│   │   ├── models/        # 数据模型 (SQLAlchemy)
│   │   ├── services/      # 业务服务 (ASR, LLM, 搜索)
│   │   └── db/            # 数据库连接、初始化
│   ├── requirements.txt
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── components/    # UI 组件
│   │   ├── pages/         # 页面
│   │   └── player/        # 视频播放器
│   ├── package.json
│   └── vite.config.ts
├── data/
│   ├── videos/            # 视频文件
│   ├── subtitles/         # 字幕文件
│   ├── summaries/         # 总结文件
│   └── embeddings/        # 向量索引
├── docker-compose.yml
└── .env.example
```

## 🚀 快速开始

### 5 分钟上手

```bash
# 1. 进入项目目录
cd course-ai-helper

# 2. 启动服务
./start.sh

# 或使用 Docker
docker-compose up -d

# 3. 访问系统
# 前端：http://localhost:3000
# API 文档：http://localhost:8000/docs
```

详细指南请查看：
- [快速开始](./QUICKSTART.md) - 5 分钟上手教程
- [部署指南](./DEPLOY.md) - 详细部署选项

## 📝 API 设计

### 认证
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/logout` - 用户登出

### 视频管理
- `GET /api/videos` - 视频列表
- `GET /api/videos/{id}` - 视频详情
- `POST /api/videos/scan` - 扫描新视频
- `POST /api/videos/{id}/favorite` - 收藏/取消收藏

### 字幕处理
- `POST /api/videos/{id}/subtitle/generate` - 生成字幕
- `GET /api/videos/{id}/subtitle` - 获取字幕

### 内容总结
- `POST /api/videos/{id}/summarize` - 生成总结
- `GET /api/videos/{id}/summary` - 获取总结
- `GET /api/videos/{id}/knowledge-points` - 获取知识点

### 搜索
- `GET /api/search?q=xxx` - 语义搜索
- `GET /api/search/suggestions` - 搜索建议

### 笔记
- `GET /api/notes` - 笔记列表
- `POST /api/notes` - 创建笔记
- `PUT /api/notes/{id}` - 更新笔记
- `DELETE /api/notes/{id}` - 删除笔记

## 🔧 核心服务

### ASR 服务
复用 subgen 核心，支持：
- Whisper / Faster-Whisper 引擎
- 批量处理
- 进度回调

### LLM 服务
支持多种后端：
- 本地：Ollama (qwen2.5, dolphin3)
- 云端：DeepSeek / OpenAI

### 向量搜索
- 嵌入模型：bge-small-zh-v1.5
- 向量数据库：ChromaDB
- 搜索范围：字幕片段 + 内容总结

## 👥 多用户设计

- JWT 认证
- 用户隔离（视频收藏、笔记、学习进度）
- 可选：共享视频库（管理员上传，所有用户可见）

## 📊 数据库设计

### users
- id, email, password_hash, created_at

### videos
- id, path, filename, duration, status, created_at

### subtitles
- id, video_id, content, language, source (asr/manual)

### summaries
- id, video_id, content, knowledge_points (JSON), created_at

### user_favorites
- user_id, video_id, created_at

### user_notes
- id, user_id, video_id, timestamp, content, tags

### embeddings
- id, video_id, text, embedding, type (subtitle/summary)

## 📝 开发计划

### ✅ 已完成
- [x] Phase 1: 基础框架 + 用户认证
- [x] Phase 2: 视频管理 + 字幕生成
- [x] Phase 3: 内容总结 + 知识点标记
- [x] Phase 4: 向量搜索 + 前端界面
- [x] Phase 5: 笔记系统 + 学习统计
- [x] Phase 6: 单元测试

### 📋 待办（详见 [TODO.md](./TODO.md)）
- [ ] WebSocket 实时进度推送
- [ ] 错误处理完善
- [ ] 视频上传功能
- [ ] 处理队列优化（Celery）
- [ ] UI/UX 优化
- [ ] 移动端适配

## 📄 License

MIT
