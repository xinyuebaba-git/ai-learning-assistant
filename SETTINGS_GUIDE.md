# ⚙️ 系统设置页面 - 使用说明

## 🎯 功能概述

设置页面允许你配置 ASR 语音识别引擎和 LLM 大模型，以满足不同的需求和硬件条件。

---

## 📍 访问设置页面

1. 登录系统
2. 点击顶部导航栏的 **"设置"** 菜单
3. 访问地址：http://localhost:3000/settings

---

## 🎤 ASR 语音识别设置

### ASR 引擎选择

| 引擎 | 说明 | 推荐度 |
|------|------|--------|
| **Faster-Whisper** | C++ 实现，速度更快，内存占用更低 | ⭐⭐⭐⭐⭐ 推荐 |
| **Whisper** | OpenAI 官方 Python 实现 | ⭐⭐⭐ |

### ASR 模型选择

| 模型 | 速度 | 精度 | 内存占用 | 适用场景 |
|------|------|------|----------|----------|
| **Tiny** | ⚡⚡⚡ 极快 | ⭐ 低 | ~100MB | 快速测试 |
| **Base** | ⚡⚡ 快 | ⭐⭐ 较低 | ~200MB | 简单内容 |
| **Small** | ⚡ 中等 | ⭐⭐⭐ 中等 | ~500MB | 日常使用 |
| **Medium** | 🐌 较慢 | ⭐⭐⭐⭐ 高 | ~1.5GB | ⭐ 推荐 |
| **Large-v3** | 🐌🐌 很慢 | ⭐⭐⭐⭐⭐ 最高 | ~3GB | 高质量要求 |
| **Turbo** | ⚡⚡⚡ 极快 | ⭐⭐⭐ 中等 | ~1GB | 平衡速度和精度 |

### 字幕分段设置

- **最大分段时长**: 每条字幕的最大时长（秒）
  - 建议：`1.6 - 2.2` 秒
  - 更短的字幕更易读，更跟画面

- **最大分段字符数**: 每条字幕的最大字符数
  - 建议：`24 - 28` 个字符
  - 短句更易读

---

## 🧠 LLM 大模型设置

### LLM 后端选择

#### 1. 本地 Ollama（推荐）

**优点**:
- ✅ 免费使用
- ✅ 数据隐私（本地处理）
- ✅ 无网络延迟

**缺点**:
- ⚠️ 需要下载模型
- ⚠️ 依赖本地硬件性能

**配置步骤**:

1. 安装 Ollama
   ```bash
   # macOS
   brew install ollama
   
   # 启动服务
   ollama serve
   ```

2. 拉取模型
   ```bash
   # 推荐模型
   ollama pull qwen2.5:7b
   
   # 其他可选模型
   ollama pull dolphin3:8b
   ollama pull huihui_ai/dolphin3-abliterated
   ```

3. 在设置页面选择模型
   - LLM 后端：本地 Ollama
   - 本地模型：选择已下载的模型
   - Ollama 服务地址：`http://localhost:11434`（默认）

#### 2. DeepSeek（云端）

**优点**:
- ✅ 效果好
- ✅ 无需本地资源
- ✅ 速度快

**缺点**:
- ⚠️ 需要 API Key（付费）
- ⚠️ 数据上传到云端

**配置步骤**:

1. 获取 API Key
   - 访问：https://platform.deepseek.com/
   - 注册并充值
   - 创建 API Key

2. 在设置页面配置
   - LLM 后端：DeepSeek
   - 模型名称：`deepseek-chat`
   - API Key：粘贴你的 API Key

#### 3. OpenAI（云端）

**优点**:
- ✅ 效果最好
- ✅ 稳定可靠

**缺点**:
- ⚠️ 价格较贵
- ⚠️ 需要国际信用卡

**配置步骤**:

1. 获取 API Key
   - 访问：https://platform.openai.com/
   - 创建 API Key

2. 在设置页面配置
   - LLM 后端：OpenAI
   - 模型名称：`gpt-4.1-mini` 或其他
   - API Key：粘贴你的 API Key

---

## 💡 推荐配置

### 配置 A: 完全免费（推荐新手）

```
ASR 引擎：Faster-Whisper
ASR 模型：Medium
LLM 后端：本地 Ollama
LLM 模型：qwen2.5:7b
```

**优点**: 完全免费，数据隐私  
**缺点**: 需要下载模型，依赖本地硬件

### 配置 B: 效果优先

```
ASR 引擎：Faster-Whisper
ASR 模型：Large-v3
LLM 后端：DeepSeek
LLM 模型：deepseek-chat
```

**优点**: 识别和总结效果最好  
**缺点**: 需要付费，数据上传云端

### 配置 C: 平衡配置

```
ASR 引擎：Faster-Whisper
ASR 模型：Medium
LLM 后端：本地 Ollama
LLM 模型：qwen2.5:14b
```

**优点**: 平衡效果和资源  
**缺点**: 需要较大内存

---

## 🔧 故障排查

### Ollama 连接失败

**问题**: 测试连接失败

**解决**:
1. 检查 Ollama 服务是否运行
   ```bash
   ollama list
   ```

2. 检查服务地址是否正确
   - 默认：`http://localhost:11434`
   - 确保端口未被占用

3. 检查模型是否已下载
   ```bash
   ollama pull qwen2.5:7b
   ```

### ASR 处理慢

**问题**: 视频处理速度很慢

**解决**:
1. 使用更小的 ASR 模型（如 Small 或 Base）
2. 使用 Faster-Whisper 而非 Whisper
3. 如果有 GPU，启用 GPU 加速

### 总结质量差

**问题**: 课程总结不准确

**解决**:
1. 使用更大的 LLM 模型
2. 切换到云端 API（DeepSeek/OpenAI）
3. 检查字幕质量，ASR 识别错误会影响总结

---

## 📊 配置保存

- ✅ 配置自动保存到后端
- ✅ 所有用户共享同一配置
- ✅ 修改配置后，新处理的视频会使用新设置
- ⚠️ 已处理的视频不会重新处理

---

## 🚀 最佳实践

1. **首次使用**: 先用小模型测试（Tiny/Base），确认系统正常
2. **日常使用**: 使用 Medium 模型，平衡速度和质量
3. **重要内容**: 使用 Large 模型或云端 API，确保质量
4. **批量处理**: 使用小模型快速处理，再手动优化重要的

---

**祝你使用愉快！** 🦞
