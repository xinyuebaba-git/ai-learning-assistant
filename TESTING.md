# 🧪 测试指南

## 后端测试

### 安装测试依赖

```bash
cd backend
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_asr.py -v

# 运行特定测试类
pytest tests/test_asr.py::TestASRService -v

# 运行特定测试函数
pytest tests/test_asr.py::TestASRService::test_init_default -v

# 带覆盖率报告
pytest tests/ -v --cov=app --cov-report=html

# 跳过慢速测试
pytest tests/ -v -m "not slow"

# 只运行集成测试
pytest tests/ -v -m integration
```

### 测试文件结构

```
backend/tests/
├── conftest.py          # 测试配置和 fixtures
├── test_asr.py          # ASR 服务测试
├── test_llm.py          # LLM 服务测试
├── test_search.py       # 搜索服务测试
└── test_api.py          # API 路由测试
```

### 测试覆盖率

```bash
# 生成 HTML 报告
pytest --cov=app --cov-report=html

# 打开报告
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov\index.html  # Windows
```

---

## 前端测试

### 安装依赖

```bash
cd frontend
npm install
```

### 运行测试

```bash
# 运行所有测试
npm run test

# 监听模式（文件变化自动重跑）
npm run test -- --watch

# 带覆盖率
npm run test -- --coverage

# 运行特定测试文件
npm run test -- src/tests/LoginPage.test.tsx

# UI 模式
npm run test -- --ui
```

### 测试文件结构

```
frontend/src/tests/
├── setup.ts             # 测试配置
├── LoginPage.test.tsx   # 登录页测试
├── RegisterPage.test.tsx # 注册页测试
└── api.test.ts          # API 客户端测试
```

---

## 快速测试脚本

### 后端测试

```bash
./test-backend.sh
```

### 前端测试

```bash
./test-frontend.sh
```

### 全部测试

```bash
./test-backend.sh && ./test-frontend.sh
```

---

## 测试最佳实践

### 1. 单元测试
- 测试单个函数/方法
- 使用 Mock 隔离依赖
- 测试边界条件
- 保持测试独立

### 2. 集成测试
- 测试模块间交互
- 使用真实数据库（测试环境）
- 测试 API 端点
- 标记为 `@pytest.mark.integration`

### 3. E2E 测试（待添加）
- 模拟真实用户流程
- 使用 Playwright 或 Cypress
- 测试关键用户路径
- 在 CI/CD 中运行

---

## 常见问题

### Q: 测试失败怎么办？
A: 查看错误信息，检查：
- 依赖是否安装
- 环境变量是否配置
- Mock 是否正确
- 测试数据是否有效

### Q: 如何跳过某些测试？
A: 使用标记：
```bash
# 跳过慢速测试
pytest -m "not slow"

# 只运行特定标记
pytest -m integration
```

### Q: 如何提高测试覆盖率？
A: 
1. 添加边界条件测试
2. 测试错误处理路径
3. 测试异常情况
4. 使用 `pytest-cov` 查看未覆盖代码

---

## CI/CD 集成（待添加）

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd backend
          pytest tests/ -v --cov=app
```

---

**测试口号**: 测试不是负担，是保障！🧪✅
