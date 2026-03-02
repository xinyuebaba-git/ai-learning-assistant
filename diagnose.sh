#!/bin/bash

# Course AI Helper - 快速诊断脚本

echo "╔════════════════════════════════════════╗"
echo "║   Course AI Helper - 系统诊断          ║"
echo "╚════════════════════════════════════════╝"
echo ""

# 1. 检查后端服务
echo "1️⃣  检查后端服务..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✅ 后端服务：运行中"
else
    echo "   ❌ 后端服务：未运行"
fi

# 2. 检查前端服务
echo "2️⃣  检查前端服务..."
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "   ✅ 前端服务：运行中"
else
    echo "   ❌ 前端服务：未运行"
fi

# 3. 检查视频文件
echo "3️⃣  检查视频文件..."
VIDEO_COUNT=$(ls -1 ../data/videos/*.mp4 ../data/videos/*.mov ../data/videos/*.mkv 2>/dev/null | wc -l)
if [ $VIDEO_COUNT -gt 0 ]; then
    echo "   ✅ 视频文件：$VIDEO_COUNT 个"
    ls -lh ../data/videos/*.mp4 ../data/videos/*.mov ../data/videos/*.mkv 2>/dev/null | awk '{print "      - "$9" ("$5")"}'
else
    echo "   ⚠️  视频文件：未找到"
fi

# 4. 检查数据库
echo "4️⃣  检查数据库..."
cd backend
source .venv/bin/activate
python3 -c "
import asyncio
from sqlalchemy import select
from app.db.base import async_session_maker
from app.models.video import Video

async def check():
    async with async_session_maker() as session:
        result = await session.execute(select(Video))
        videos = result.scalars().all()
        print(f'   ✅ 数据库视频：{len(videos)} 个')
        for v in videos:
            print(f'      - {v.filename[:50]}...')

asyncio.run(check())
" 2>/dev/null
cd ..

# 5. 测试 API
echo "5️⃣  测试 API..."
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser2","password":"password123"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -n "$TOKEN" ]; then
    echo "   ✅ API 登录：成功"
    
    VIDEO_API=$(curl -s http://localhost:8000/api/videos -H "Authorization: Bearer $TOKEN")
    if echo "$VIDEO_API" | python3 -c "import sys,json; data=json.load(sys.stdin); print(f'   ✅ 视频 API: 返回 {len(data)} 个视频')" 2>/dev/null; then
        :
    else
        echo "   ❌ 视频 API: 失败"
    fi
else
    echo "   ❌ API 登录：失败"
fi

echo ""
echo "════════════════════════════════════════"
echo "诊断完成！"
echo ""
echo "📝 建议操作:"
echo "  1. 访问 http://localhost:3000/test.html 进行详细测试"
echo "  2. 打开浏览器控制台查看错误信息 (F12)"
echo "  3. 检查是否已登录"
echo ""
