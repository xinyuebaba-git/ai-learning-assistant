# 视频播放兼容性解决方案

## 📋 问题背景

某些视频文件无法在网页前端播放，报错 `MEDIA_ERR_DECODE (3)`，但使用本地播放器（如 QuickTime、VLC）可以正常播放。

## 🔍 根本原因

视频文件的**容器格式**不是浏览器兼容的 MP4 格式。

### 常见不兼容格式
- **MPEG-TS** (`.ts`, `.mts`) - 广播/流媒体格式
- **MKV** - Matroska 容器
- **AVI** - 老旧容器
- **WMV** - Windows Media

### 浏览器兼容格式
浏览器原生支持的 MP4 容器：
- `mov,mp4,m4a,3gp,3g2,mj2`

## ✅ 解决方案

### 自动转码流程

1. **扫描视频时检查格式**
   ```bash
   ffprobe -v error -show_entries format=format_name -of json <video_file>
   ```

2. **判断是否兼容**
   ```python
   COMPATIBLE_FORMATS = {"mov", "mp4", "m4a", "3gp", "3g2", "mj2"}
   is_compatible = any(f in format_name for f in COMPATIBLE_FORMATS)
   ```

3. **不兼容则转码**
   ```bash
   ffmpeg -y -i input.mp4 \
     -c:v libx264 \
     -c:a aac \
     -movflags +faststart \
     output.mp4
   ```

### 参数说明
- `-c:v libx264` - 使用 H.264 视频编码
- `-c:a aac` - 使用 AAC 音频编码
- `-movflags +faststart` - 优化 Web 播放（moov atom 前置）

## 📝 实现细节

### 后端 API 修改

文件：`backend/app/api/videos.py`

```python
@router.post("/scan")
async def scan_videos(...):
    # 1. 扫描视频文件
    # 2. 检查每个视频的格式
    # 3. 不兼容则自动转码
    # 4. 转码失败则记录日志并标记状态
```

### 转码失败处理

如果转码失败：
1. 恢复原始备份文件
2. 视频记录状态标记为 `transcode_failed`
3. 记录详细错误日志
4. 返回统计信息供人工介入

## 🧪 测试方法

### 1. 检查当前视频格式
```bash
cd ~/.openclaw/workspace/course-ai-helper
./test-video-transcode.sh
```

### 2. 手动测试单个视频
```bash
# 检查格式
ffprobe -v error -show_entries format=format_name \
  -of default=noprint_wrappers=1 \
  "video.mp4"

# 转码测试
ffmpeg -y -i "video.mp4" \
  -c:v libx264 -c:a aac -movflags +faststart \
  "video_transcoded.mp4"
```

### 3. 验证转码结果
```bash
# 验证格式
ffprobe -v error -show_entries format=format_name \
  -of default=noprint_wrappers=1 \
  "video_transcoded.mp4"

# 应该输出：mov,mp4,m4a,3gp,3g2,mj2
```

## 📊 实际案例

### 案例：20.1 用频率估计概率.mp4

**问题现象：**
- 前端播放报错：`MEDIA_ERR_DECODE (3)`
- 本地播放正常

**诊断结果：**
```bash
$ ffprobe -v error -show_entries format=format_name file.mp4
format_name=mpegts  # ← 问题所在
```

**解决方案：**
```bash
ffmpeg -y -i "20.1 用频率估计概率.mp4.backup" \
  -c:v libx264 -c:a aac -movflags +faststart \
  "20.1 用频率估计概率.mp4"
```

**结果：**
- ✅ 格式从 `mpegts` 变为 `mov,mp4,m4a...`
- ✅ 文件大小从 51MB 优化到 24MB
- ✅ 前端播放正常

## 🔧 维护指南

### 日志位置
```
~/.openclaw/workspace/course-ai-helper/logs/backend.log
```

### 转码失败处理
1. 查看后端日志，找到失败原因
2. 手动执行转码命令测试
3. 如果手动转码成功，检查权限问题
4. 如果手动转码失败，考虑：
   - 视频文件损坏
   - 缺少编解码器
   - 磁盘空间不足

### 性能优化建议
- 大文件转码可能需要较长时间（5-10 分钟）
- 考虑异步转码（Celery 任务）
- 限制并发转码数量
- 设置合理的超时时间（默认 600 秒）

## 📚 相关资源

- [ffmpeg 官方文档](https://ffmpeg.org/documentation.html)
- [H.264 编码参数详解](https://trac.ffmpeg.org/wiki/Encode/H.264)
- [浏览器媒体格式支持](https://developer.mozilla.org/en-US/docs/Web/HTML/Supported_media_formats)

---

**创建时间：** 2026-03-04  
**最后更新：** 2026-03-04  
**维护者：** 公司小龙虾 🦞
