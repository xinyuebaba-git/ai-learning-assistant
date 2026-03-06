#!/bin/bash
# 两阶段知识点生成 - 使用后端 API

VIDEO_ID=${1:-1}

echo "========================================="
echo "两阶段知识点生成 - 视频 $VIDEO_ID"
echo "========================================="
echo ""

# 阶段 1：生成知识点（不带时间戳）
echo "📡 阶段 1：生成知识点..."
STAGE1_RESULT=$(curl -s -X POST "http://localhost:8000/api/videos/$VIDEO_ID/generate-kp" \
  -H "Content-Type: application/json" \
  -d '{"stage": 1}' 2>/dev/null)

echo "$STAGE1_RESULT" | python3 -m json.tool 2>/dev/null || echo "$STAGE1_RESULT"

echo ""
echo "========================================="
echo "阶段 1 完成"
echo "========================================="
