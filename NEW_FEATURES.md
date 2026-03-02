# 🆕 新增功能说明

## 2026-03-02 更新

### ✅ 已添加功能

#### 1. Deepgram ASR 引擎支持

**说明**: 新增 Deepgram 云端 ASR 引擎，提供极速语音识别。

**配置方法**:
1. 访问设置页面：http://localhost:3000/settings
2. ASR 引擎选择：`Deepgram (云端 API)`
3. 输入 Deepgram API Key
4. 选择模型：
   - `Nova-3` - 最快，推荐
   - `Nova-2` - 平衡
   - `Enhanced` - 增强版
   - `Base` - 基础版

**获取 API Key**:
- 访问：https://console.deepgram.com/
- 注册账号
- 创建 API Key

**优点**:
- ⚡ 速度极快（云端处理）
- 🎯 精度高
- 💰 按使用量付费

**缺点**:
- ⚠️ 需要网络
- ⚠️ 数据上传到云端

---

#### 2. 阿里百炼大模型支持

**说明**: 新增阿里百炼（通义千问）大模型支持，使用专用接入 URL。

**配置方法**:
1. 访问设置页面：http://localhost:3000/settings
2. LLM 后端选择：`阿里百炼 (云端)`
3. 输入 API Key
4. 配置 Base URL：`https://dashscope.aliyuncs.com/compatible-mode/v1`
5. 选择模型：
   - `qwen-plus` - 推荐
   - `qwen-max` - 最强
   - `qwen-turbo` - 最快

**获取 API Key**:
- 访问：https://bailian.console.aliyun.com/
- 注册/登录阿里云账号
- 开通百炼服务
- 创建 API Key

**接入 URL**:
```
https://dashscope.aliyuncs.com/compatible-mode/v1
```

**优点**:
- 🇨🇳 中文优化好
- 💰 价格适中
- 🚀 国内访问快

**缺点**:
- ⚠️ 需要网络
- ⚠️ 数据上传到云端

---

### 🎯 推荐配置组合

#### 配置 A: 完全免费
```
ASR 引擎：Faster-Whisper
ASR 模型：Medium
LLM 后端：本地 Ollama
LLM 模型：qwen2.5:7b
```

#### 配置 B: 云端高速
```
ASR 引擎：Deepgram
ASR 模型：Nova-3
LLM 后端：阿里百炼
LLM 模型：qwen-plus
```

#### 配置 C: 混合配置
```
ASR 引擎：Faster-Whisper (本地)
ASR 模型：Medium
LLM 后端：阿里百炼 (云端)
LLM 模型：qwen-plus
```

---

### 📊 价格参考

#### Deepgram ASR
- 按音频时长计费
- 约 $0.0059/分钟 (Nova-3)
- 1 小时音频 ≈ $0.35

#### 阿里百炼
- 按 Token 计费
- qwen-plus: ¥0.002/1K tokens
- 1000 字总结 ≈ ¥0.02

---

### 🔧 技术细节

#### Deepgram API 实现
- 使用 HTTP POST 发送音频
- 返回 JSON 格式字幕
- 自动语言检测
- 智能分词和标点

#### 阿里百炼实现
- 兼容 OpenAI API 格式
- 使用专用接入点
- 支持流式输出
- 自动重试机制

---

### 📝 使用示例

#### 1. 配置 Deepgram ASR

```bash
# 在设置页面配置
ASR 引擎：Deepgram
ASR 模型：Nova-3
API Key: dg_xxxxxxxxxx
```

#### 2. 配置阿里百炼

```bash
# 在设置页面配置
LLM 后端：阿里百炼
模型：qwen-plus
API Key: sk-xxxxxxxxxx
Base URL: https://dashscope.aliyuncs.com/compatible-mode/v1
```

#### 3. 处理视频

配置完成后，处理视频时会自动使用新配置：
1. 访问视频库
2. 点击视频
3. 点击"开始处理"
4. 等待完成

---

### ⚠️ 注意事项

1. **API Key 安全**
   - 不要分享 API Key
   - 定期更换
   - 设置使用限额

2. **网络要求**
   - Deepgram 需要访问国际网络
   - 阿里百炼国内可直接访问

3. **费用控制**
   - 设置预算提醒
   - 监控使用量
   - 及时处理不需要的视频

4. **数据隐私**
   - 云端处理会上传数据
   - 敏感内容建议使用本地模型

---

### 🐛 故障排查

#### Deepgram 连接失败
1. 检查 API Key 是否正确
2. 检查网络连接
3. 查看后端日志

#### 阿里百炼返回错误
1. 检查 Base URL 是否正确
2. 检查 API Key 是否有效
3. 确认账户余额充足

---

**更新时间**: 2026-03-02  
**维护者**: 公司小龙虾 🦞
