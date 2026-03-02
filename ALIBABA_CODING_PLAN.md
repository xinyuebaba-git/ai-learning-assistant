# 🔧 阿里百炼 Coding Plan 配置说明

## 📍 官方文档

**参考文档**: [阿里百炼 Coding Plan 快速入门](https://help.aliyun.com/zh/model-studio/coding-plan-quickstart)

---

## 🌐 Base URL 配置

### ✅ 正确的接入地址

```
https://coding.dashscope.aliyuncs.com/v1
```

### ❌ 错误的地址

```
# 这是普通 DashScope 的地址
https://dashscope.aliyuncs.com/compatible-mode/v1

# 这也是错误的
https://dashscope.aliyuncs.com/compatible-mode/v1/coding-plan
```

---

## ⚙️ 配置方法

### 方式 1: 通过设置页面（推荐）

1. 访问：http://localhost:3000/settings
2. LLM 后端选择：`阿里百炼 (云端)`
3. 配置以下参数：

```
模型名称：qwen-coder-plus
API Key: sk-xxxxxxxxxx
Base URL: https://dashscope.aliyuncs.com/compatible-mode/v1/coding-plan
```

### 方式 2: 环境变量

```bash
export ALIBABA_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1/coding-plan"
export ALIBABA_MODEL="qwen-coder-plus"
export ALIBABA_API_KEY="sk-xxxxxxxxxx"
```

### 方式 3: 配置文件

编辑 `backend/config/settings.json`:

```json
{
  "alibaba_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/coding-plan",
  "alibaba_model": "qwen-coder-plus",
  "alibaba_api_key": "sk-xxxxxxxxxx"
}
```

---

## 📋 支持的模型

Coding Plan 支持以下模型：

| 模型 | 说明 | 推荐场景 |
|------|------|----------|
| **qwen-coder-plus** | 最强代码能力 | ⭐ 推荐 |
| **qwen-coder** | 标准代码能力 | 日常使用 |
| **qwen-plus** | 通用模型 | 文本总结 |
| **qwen-max** | 最强通用 | 复杂任务 |

---

## 💰 价格参考

| 模型 | 输入价格 | 输出价格 |
|------|----------|----------|
| qwen-coder-plus | ¥0.0035/1K tokens | ¥0.007/1K tokens |
| qwen-coder | ¥0.002/1K tokens | ¥0.004/1K tokens |
| qwen-plus | ¥0.002/1K tokens | ¥0.004/1K tokens |

**示例**:
- 1000 字课程总结 ≈ ¥0.02
- 1 小时视频处理 ≈ ¥0.5-1.0

---

## 🔑 获取 API Key

1. 访问：https://bailian.console.aliyun.com/
2. 登录阿里云账号
3. 开通百炼服务
4. 创建 API Key
5. 确保账户有足够余额

---

## 🧪 测试连接

配置完成后，可以通过以下方式测试：

### 方式 1: 使用 API 测试

```bash
# 获取 Token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 获取配置
curl -s http://localhost:8000/api/settings \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### 方式 2: 直接调用

```bash
curl -X POST https://dashscope.aliyuncs.com/compatible-mode/v1/coding-plan/chat/completions \
  -H "Authorization: Bearer sk-xxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-coder-plus",
    "messages": [
      {"role": "user", "content": "Hello"}
    ]
  }'
```

---

## ⚠️ 常见问题

### Q1: 401 Unauthorized

**原因**: API Key 无效或过期

**解决**:
1. 检查 API Key 是否正确
2. 确认账户余额充足
3. 重新生成 API Key

### Q2: 404 Not Found

**原因**: Base URL 错误

**解决**:
- 确保使用：`https://dashscope.aliyuncs.com/compatible-mode/v1/coding-plan`
- 不要漏掉 `/coding-plan` 后缀

### Q3: 连接超时

**原因**: 网络问题

**解决**:
1. 检查网络连接
2. 尝试使用国内节点
3. 联系阿里云支持

---

## 📊 监控使用量

1. 访问：https://bailian.console.aliyun.com/
2. 查看"用量统计"
3. 设置预算提醒
4. 定期导出账单

---

## 🔒 安全建议

1. **保护 API Key**
   - 不要提交到代码仓库
   - 不要分享给他人
   - 定期更换

2. **设置限额**
   - 在阿里云控制台设置每日/每月限额
   - 开启余额提醒

3. **监控异常**
   - 定期检查使用量
   - 发现异常立即停用 API Key

---

## 📖 相关文档

- [Coding Plan 快速入门](https://help.aliyun.com/zh/model-studio/coding-plan-quickstart)
- [API 参考文档](https://help.aliyun.com/zh/model-studio/api-reference)
- [计费说明](https://help.aliyun.com/zh/model-studio/pricing)

---

**更新时间**: 2026-03-02  
**维护者**: 公司小龙虾 🦞
