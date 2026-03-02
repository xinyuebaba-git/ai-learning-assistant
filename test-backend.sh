#!/bin/bash

# 运行后端测试
echo "🧪 运行后端测试..."
cd backend
source .venv/bin/activate 2>/dev/null || true
pytest tests/ -v --cov=app --cov-report=term-missing
cd ..

echo ""
echo "✅ 后端测试完成"
