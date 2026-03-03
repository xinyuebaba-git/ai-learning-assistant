# Architect Agent - 系统架构评审报告

**评审者**: Architect Agent (by main Agent)  
**评审时间**: 2026-03-03  
**评审对象**: Course AI Helper 项目

---

## 📊 总体评价

**架构评分**: ⭐⭐⭐⭐ (4/5)

项目采用现代 Web 应用架构，前后端分离，服务层抽象良好。整体设计合理，适合当前规模，具备良好的扩展基础。

---

## ✅ 架构优点（5 点）

### 1. 清晰的分层架构
```
前端层 (React) → API 层 (FastAPI) → 服务层 → 数据层
```
- 职责明确，易于维护
- 符合关注点分离原则
- 便于团队协作

### 2. 技术栈选型合理
- **前端**: React 18 + TypeScript + TailwindCSS - 现代、高效
- **后端**: Python 3.11 + FastAPI - 异步性能优秀
- **数据库**: SQLite (开发) + ChromaDB (向量) - 轻量且功能完备
- **AI 服务**: Faster-Whisper + Ollama - 可本地部署

### 3. 异步处理设计
- 使用 Async SQLAlchemy
- 支持并发请求
- 为后续任务队列预留空间

### 4. 服务层抽象良好
```python
ASRService → 支持 Whisper/Faster-Whisper 切换
LLMService → 支持本地/云端多后端
SearchService → 封装 ChromaDB 复杂度
```

### 5. RESTful API 设计
- 资源导向的 URL 设计
- 标准的 HTTP 方法使用
- 统一的状态码和错误处理

---

## ⚠️ 发现的问题和风险

### 严重问题 (P0)

#### 1. 视频处理同步阻塞
**问题**: `VideoProcessingService.process_video()` 同步执行
```python
# processor.py - 阻塞整个请求
await self._generate_subtitles(video)  # 可能 10-30 分钟
await self._generate_summary(video)    # 可能 1-5 分钟
await self._create_embeddings(video)   # 可能 5-10 分钟
```

**影响**:
- API 请求超时（默认 60s）
- 用户界面卡顿
- 无法并发处理多个视频

**风险等级**: 🔴 高

---

#### 2. 数据库状态不一致
**问题**: 视频 1 的 `has_summary=1` 但 `status=FAILED`
```sql
-- 当前状态
id=1, status='FAILED', has_subtitle=1, has_summary=1
```

**影响**:
- 前端显示混乱
- 业务逻辑判断错误
- 用户体验差

**风险等级**: 🔴 高

---

### 重要问题 (P1)

#### 3. 缺少任务队列
**问题**: 无 Celery/RQ 等异步任务系统

**影响**:
- 无法后台处理视频
- 无法重试失败任务
- 无法查看处理进度

**风险等级**: 🟡 中

---

#### 4. 错误处理不完善
**问题**: 
- LLM 服务 JSON 解析失败无重试
- ASR 失败无降级方案
- 网络异常无自动重试

**影响**:
- 视频处理易失败
- 需要手动干预

**风险等级**: 🟡 中

---

#### 5. 数据库设计缺陷
**问题**: 
- 从 PostgreSQL 降级为 SQLite（可能是开发环境）
- 缺少数据库迁移脚本（Alembic）
- 缺少索引优化

**影响**:
- 生产环境性能问题
- 数据结构变更困难

**风险等级**: 🟡 中

---

### 一般问题 (P2)

#### 6. 缺少 API 版本控制
**问题**: 无 `/api/v1/` 前缀

**影响**: 后续升级困难

---

#### 7. 配置管理分散
**问题**: 配置在 `config.py` 和环境变量间混用

**影响**: 部署复杂

---

#### 8. 缺少监控和日志聚合
**问题**: 
- 使用 Loguru 但无集中收集
- 无 Prometheus/Grafana 监控
- 无错误追踪（Sentry）

**影响**: 问题排查困难

---

## 💡 改进建议

### 短期（1-2 周）- 优先级 P0

#### 1. 修复数据库状态不一致
```bash
# 执行 SQL 修复
UPDATE videos SET status='SUMMARIZED' 
WHERE id=1 AND has_summary=1 AND status='FAILED';
```

**预计工时**: 1h

#### 2. 优化 LLM 提示词
**当前问题**: 总结返回空字符串

**建议**:
```python
system_prompt = """你是教育内容专家。请分析视频字幕并生成：
1. 内容总结（200-300 字）
2. 知识点列表（10-15 个，包含时间戳）

输出 JSON 格式：
{
  "summary": "总结内容",
  "knowledge_points": [
    {"timestamp": 120.5, "title": "知识点标题", "type": "concept"}
  ]
}

只返回 JSON，不要其他内容。"""
```

**预计工时**: 2h

#### 3. 添加任务队列基础框架
**方案**: 使用 RQ（Redis Queue）- 轻量级
```python
# tasks.py
from rq import Queue
from redis import Redis

queue = Queue('video_processing', connection=Redis())

# API 路由
@router.post("/{video_id}/process")
async def process_video(video_id: int):
    queue.enqueue(process_video_task, video_id)
    return {"status": "queued", "job_id": job.id}
```

**预计工时**: 8h

---

### 中期（1 个月）- 优先级 P1

#### 4. 实现 WebSocket 进度推送
```python
# 前端轮询或 WebSocket
@router.get("/{video_id}/progress")
async def get_progress(video_id: int):
    return {"status": "processing", "progress": 0.6}
```

**预计工时**: 6h

#### 5. 添加数据库迁移
**工具**: Alembic
```bash
alembic init alembic
alembic revision --autogenerate -m "Initial"
```

**预计工时**: 4h

#### 6. 完善错误处理和重试
```python
from tenacity import retry, stop_after_attempt

@retry(stop=stop_after_attempt(3))
async def generate_summary(video: Video):
    # LLM 调用
```

**预计工时**: 4h

---

### 长期（3 个月）- 优先级 P2

#### 7. 升级到 PostgreSQL（生产环境）
**理由**:
- 更好的并发支持
- 更强大的查询能力
- 更好的数据完整性

**预计工时**: 16h

#### 8. 添加监控和告警
**工具栈**:
- Prometheus + Grafana（指标监控）
- Sentry（错误追踪）
- ELK Stack（日志聚合）

**预计工时**: 24h

---

## 📋 技术债务清单

| 债务项 | 严重程度 | 预计工时 | 优先级 |
|--------|----------|----------|--------|
| 视频处理阻塞 | 高 | 8h | P0 |
| 数据库状态不一致 | 高 | 1h | P0 |
| LLM 提示词优化 | 高 | 2h | P0 |
| 缺少任务队列 | 中 | 8h | P1 |
| 错误处理不完善 | 中 | 4h | P1 |
| 数据库迁移缺失 | 中 | 4h | P1 |
| 缺少 API 版本控制 | 低 | 2h | P2 |
| 监控缺失 | 低 | 24h | P2 |

**总技术债务**: ~53 小时

---

## 🎯 架构演进路线图

### Phase 1: 稳定性提升（2 周）
- [x] 修复数据库状态
- [ ] 优化 LLM 提示词
- [ ] 添加基础任务队列
- [ ] 完善错误处理

### Phase 2: 可扩展性（1 个月）
- [ ] 实现 WebSocket 进度推送
- [ ] 添加数据库迁移
- [ ] 性能优化（索引、缓存）
- [ ] API 版本控制

### Phase 3: 生产就绪（3 个月）
- [ ] 升级到 PostgreSQL
- [ ] 添加监控告警
- [ ] CI/CD 流水线
- [ ] 负载均衡

---

## 📊 架构健康度评估

```
代码结构：    ⭐⭐⭐⭐⭐ (5/5) - 分层清晰
技术选型：    ⭐⭐⭐⭐ (4/5) - 现代合理
可扩展性：    ⭐⭐⭐ (3/5) - 有基础待完善
性能优化：    ⭐⭐⭐ (3/5) - 基本满足
可维护性：    ⭐⭐⭐⭐ (4/5) - 代码质量好
安全性：      ⭐⭐⭐⭐ (4/5) - JWT 认证完善

综合评分：    ⭐⭐⭐⭐ (3.8/5)
```

---

## 🏁 结论

**项目架构整体良好**，采用现代技术栈，分层清晰，适合当前业务规模。

**关键待解决问题**:
1. 视频处理异步化（任务队列）
2. LLM 总结生成优化
3. 数据库状态修复

**建议优先处理 P0 问题**，然后逐步完善 P1/P2 项目。

项目具备良好的扩展基础，按路线图演进可成为生产级系统。

---

*报告生成时间：2026-03-03*  
*评审者：Architect Agent (公司小龙虾 🦞 代)*
