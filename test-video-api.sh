#!/bin/bash

# 视频 API 测试脚本

API_BASE="http://localhost:8000"
TOKEN=$(cat .env | grep "JWT_SECRET" | cut -d'=' -f2 || echo "test_token")

echo "🎬 视频 API 测试"
echo "================"

# 获取 token（需要先登录）
echo -e "\n1️⃣  登录获取 token..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')

echo "登录响应：$LOGIN_RESPONSE"

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "❌ 获取 token 失败，请检查登录凭证"
  exit 1
fi

echo "✅ Token: ${TOKEN:0:20}..."

# 获取视频列表
echo -e "\n2️⃣  获取视频列表..."
VIDEO_LIST=$(curl -s "$API_BASE/api/videos" \
  -H "Authorization: Bearer $TOKEN")

echo "视频列表：$VIDEO_LIST" | head -50

# 提取第一个视频 ID
VIDEO_ID=$(echo $VIDEO_LIST | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -z "$VIDEO_ID" ]; then
  echo "❌ 没有找到视频"
  exit 1
fi

echo "✅ 使用视频 ID: $VIDEO_ID"

# 获取视频详情
echo -e "\n3️⃣  获取视频详情..."
VIDEO_DETAIL=$(curl -s "$API_BASE/api/videos/$VIDEO_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "视频详情：$VIDEO_DETAIL" | head -50

# 测试视频流
echo -e "\n4️⃣  测试视频流..."
STREAM_RESPONSE=$(curl -s -I "$API_BASE/api/videos/$VIDEO_ID/stream" \
  -H "Authorization: Bearer $TOKEN")

echo "视频流响应头："
echo "$STREAM_RESPONSE" | head -20

# 获取字幕
echo -e "\n5️⃣  获取字幕..."
SUBTITLE_RESPONSE=$(curl -s "$API_BASE/api/videos/$VIDEO_ID/subtitle" \
  -H "Authorization: Bearer $TOKEN")

echo "字幕响应：$SUBTITLE_RESPONSE" | head -50

# 获取总结
echo -e "\n6️⃣  获取总结..."
SUMMARY_RESPONSE=$(curl -s "$API_BASE/api/videos/$VIDEO_ID/summary" \
  -H "Authorization: Bearer $TOKEN")

echo "总结响应：$SUMMARY_RESPONSE" | head -50

echo -e "\n✅ 测试完成！"
