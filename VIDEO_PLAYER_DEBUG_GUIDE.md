# 🎬 视频播放器调试指南

**创建时间**: 2026-03-04 00:10  
**状态**: 🔍 调试中

---

## ✅ 系统状态检查

### 后端服务
- ✅ 运行正常 (HTTP 200)
- ✅ 视频文件存在 (3 个，共 725MB)
- ✅ API 响应正常 (视频 1/2/3 都是 HTTP 200)

### 前端服务
- ✅ Vite 运行正常 (http://localhost:3000)
- ✅ 代码已热更新

---

## 🧹 清除浏览器缓存（重要！）

### 方法 1: 强制刷新（推荐）

**在视频播放页面按**:
- **Mac**: `Cmd + Shift + R`
- **Windows**: `Ctrl + Shift + R`

### 方法 2: 开发者工具清除

1. 按 `F12` 打开开发者工具
2. **右键点击**浏览器刷新按钮
3. 选择 "**清空缓存并硬性重新加载**"

### 方法 3: 禁用缓存（开发模式）

1. 按 `F12` 打开开发者工具
2. 进入 **Network** 标签
3. 勾选 **Disable cache**
4. **保持开发者工具打开**
5. 刷新页面

---

## 📝 查看详细日志

### 步骤 1: 打开开发者工具

按 `F12` 或右键 → 检查

### 步骤 2: 查看 Console 标签

你应该看到以下日志：

```
🎬 [VideoPlayerPage] 页面加载，video id: 1
📹 [VideoPlayerPage] 开始获取视频数据，id: 1
✅ [VideoPlayerPage] 视频数据获取成功：05.【文言】《桃花源记》课内文言文精讲.mp4
🎥 [VideoPlayer] 组件渲染，src: /api/videos/1/play
🎥 [VideoPlayer] 参数：{src: "...", poster: "", subtitles: 3636, knowledgePoints: 19}
⚙️ [VideoPlayer] 开始初始化 Video.js
⚙️ [VideoPlayer] videoRef: 存在
```

### 步骤 3: 查看 Network 标签

1. 刷新页面
2. 点击视频
3. 查找 `play` 请求
4. 检查：
   - **Status**: 应该是 `200` 或 `206` (Partial Content)
   - **Type**: 应该是 `media`
   - **Size**: 应该是几百 MB
   - **Content-Type**: 应该是 `video/mp4`

### 步骤 4: 查看 Elements 标签

1. 搜索 `video` 元素
2. 检查是否存在：
```html
<video class="video-js vjs-default-skin..." ...>
  <source src="/api/videos/1/play" type="video/mp4">
</video>
```

---

## 🐛 常见错误及解决方案

### 错误 1: "videoRef: 不存在"

**原因**: DOM 未正确渲染

**解决**:
1. 清除缓存
2. 硬刷新
3. 检查 React 组件是否正确挂载

### 错误 2: "Failed to load video"

**原因**: 视频源 URL 错误或 CORS 问题

**解决**:
1. 检查 Network 标签的请求 URL
2. 检查是否有 CORS 错误
3. 检查后端日志

### 错误 3: "No compatible source was found"

**原因**: 浏览器不支持视频格式

**解决**:
1. 检查视频编码格式（应该是 H.264 + AAC）
2. 尝试其他浏览器（Chrome/Edge/Firefox）
3. 检查 `<source>` 标签的 type 属性

### 错误 4: 播放器显示但无法点击

**原因**: Video.js 未正确初始化

**解决**:
1. 检查 Console 是否有初始化错误
2. 检查 videoRef 是否正确绑定
3. 清除缓存并刷新

---

## 🔍 手动测试

### 测试 1: 直接访问视频 URL

在浏览器地址栏输入：
```
http://localhost:8000/api/videos/1/play
```

**预期**: 浏览器应该开始下载或播放视频

### 测试 2: 使用 curl 测试

```bash
curl -I http://localhost:8000/api/videos/1/play
```

**预期输出**:
```
HTTP/1.1 200 OK
content-type: video/mp4
content-length: 391925831
```

### 测试 3: 检查视频元素

在浏览器 Console 执行：
```javascript
document.querySelector('video')
```

**预期**: 应该返回 video 元素

---

## 📊 日志输出示例

### 正常日志

```
🎬 [VideoPlayerPage] 页面加载，video id: 1
📹 [VideoPlayerPage] 开始获取视频数据，id: 1
✅ [VideoPlayerPage] 视频数据获取成功：05.【文言】《桃花源记》课内文言文精讲.mp4
🎥 [VideoPlayer] 组件渲染，src: /api/videos/1/play
🎥 [VideoPlayer] 参数：{src: "/api/videos/1/play", poster: "", subtitles: 3636, knowledgePoints: 19}
⚙️ [VideoPlayer] 开始初始化 Video.js
⚙️ [VideoPlayer] videoRef: 存在
📹 [VideoPlayer] 视频加载成功，时长：2700
```

### 错误日志示例

```
❌ [VideoPlayerPage] 视频数据获取失败：...
或
❌ [VideoPlayer] 视频播放错误：...
或
⚙️ [VideoPlayer] videoRef: 不存在
```

---

## 🎯 验收步骤

1. **清除缓存** (Cmd + Shift + R)
2. **打开开发者工具** (F12)
3. **进入 Network 标签**，勾选 "Disable cache"
4. **刷新页面**
5. **点击任意视频**
6. **观察 Console 日志** - 应该看到上述正常日志
7. **观察 Network 请求** - 应该看到视频流请求
8. **检查视频播放** - 应该可以播放

---

## 📞 报告问题

如果仍然无法播放，请提供以下信息：

1. **浏览器 Console 截图** (F12 → Console)
2. **Network 标签截图** (F12 → Network → 筛选 "play")
3. **Elements 标签截图** (F12 → Elements → 搜索 "video")
4. **使用的浏览器及版本**

---

*最后更新：2026-03-04 00:10*
