#!/bin/bash

# 运行前端测试
echo "🧪 运行前端测试..."
cd frontend
npm install 2>/dev/null || true
npm run test
cd ..

echo ""
echo "✅ 前端测试完成"
