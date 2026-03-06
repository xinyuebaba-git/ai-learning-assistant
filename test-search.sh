#!/bin/bash

echo "========================================="
echo "搜索功能完整测试"
echo "========================================="
echo ""

# 测试 1: 后端 API
echo "📋 测试 1: 后端 API（中文关键词）"
result=$(curl -sG "http://localhost:8000/api/search" \
  --data-urlencode "q=陶渊明" \
  --data-urlencode "limit=5" 2>/dev/null)

if echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if d['total'] > 0 else 1)" 2>/dev/null; then
  total=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin)['total'])")
  echo "✅ 通过 - 返回 $total 条结果"
else
  echo "❌ 失败 - 无结果或 API 错误"
  echo "$result" | python3 -m json.tool 2>/dev/null || echo "$result"
fi
echo ""

# 测试 2: Vite 代理
echo "📋 测试 2: Vite 代理（前端访问）"
result=$(curl -sG "http://localhost:3000/api/search" \
  --data-urlencode "q=陶渊明" \
  --data-urlencode "limit=5" 2>/dev/null)

if echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if d['total'] > 0 else 1)" 2>/dev/null; then
  total=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin)['total'])")
  echo "✅ 通过 - 返回 $total 条结果"
else
  echo "❌ 失败 - 无结果或 API 错误"
  echo "$result" | python3 -m json.tool 2>/dev/null || echo "$result"
fi
echo ""

# 测试 3: 英文关键词
echo "📋 测试 3: 英文关键词测试"
result=$(curl -sG "http://localhost:8000/api/search" \
  --data-urlencode "q=probability" \
  --data-urlencode "limit=5" 2>/dev/null)

if echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0)" 2>/dev/null; then
  total=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin)['total'])")
  echo "✅ 通过 - 返回 $total 条结果"
else
  echo "❌ 失败"
fi
echo ""

# 测试 4: 空关键词
echo "📋 测试 4: 空关键词验证（应该返回 400）"
status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/search?q=" 2>/dev/null)
if [ "$status" = "400" ]; then
  echo "✅ 通过 - 正确返回 400 错误"
else
  echo "⚠️  警告 - 返回状态码：$status"
fi
echo ""

# 测试 5: 搜索建议
echo "📋 测试 5: 搜索建议 API"
result=$(curl -sG "http://localhost:8000/api/search/suggestions" \
  --data-urlencode "q=桃花源" \
  --data-urlencode "limit=5" 2>/dev/null)

if echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if 'suggestions' in d else 1)" 2>/dev/null; then
  echo "✅ 通过 - 返回建议列表"
  echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print('  建议:', d.get('suggestions', []))"
else
  echo "❌ 失败"
  echo "$result" | python3 -m json.tool 2>/dev/null || echo "$result"
fi
echo ""

# 测试 6: 数据库连接
echo "📋 测试 6: 数据库字幕数据验证"
count=$(sqlite3 ~/.openclaw/workspace/course-ai-helper/backend/data/course_ai.db \
  "SELECT COUNT(*) FROM subtitles WHERE text LIKE '%陶渊明%';" 2>/dev/null)
if [ "$count" -gt 0 ]; then
  echo "✅ 通过 - 数据库包含 $count 条相关字幕"
else
  echo "❌ 失败 - 数据库无相关数据"
fi
echo ""

echo "========================================="
echo "测试完成"
echo "========================================="
