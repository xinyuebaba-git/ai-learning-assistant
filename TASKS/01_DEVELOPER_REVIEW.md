# Developer Agent 任务：代码审查和熟悉

## 📋 任务说明

请阅读项目代码，全面了解代码结构和实现细节，为后续开发做准备。

## 📚 需要阅读的材料

1. **项目简报**: `AGENT_TEAM_BRIEF.md`
2. **后端代码**: `backend/app/` 目录
   - `api/videos.py` - 视频管理 API
   - `services/processor.py` - 视频处理服务
   - `services/llm.py` - LLM 服务
   - `services/asr.py` - ASR 服务
3. **前端代码**: `frontend/src/` 目录
   - `pages/VideoPlayerPage.tsx` - 播放器页面
   - `pages/VideoListPage.tsx` - 视频列表
   - `api/index.ts` - API 客户端
4. **数据库模型**: `backend/app/models/video.py`

## 🎯 审查重点

1. **代码质量**
   - 代码规范遵循情况
   - 代码复用性
   - 错误处理是否完善

2. **功能实现**
   - 视频流 API 实现
   - 视频处理流程
   - 字幕和总结生成

3. **性能问题**
   - 有无性能瓶颈？
   - 数据库查询是否优化？
   - 有无 N+1 查询问题？

4. **安全问题**
   - 认证授权是否完善？
   - 有无 SQL 注入风险？
   - 文件上传是否安全？

## 📝 输出要求

请提供一份代码审查报告，包含：
- 代码质量评估
- 发现的 Bug 和问题
- 性能优化建议
- 代码重构建议

## ⏰ 完成时间

请在阅读完成后输出报告。
