#!/bin/bash

# 视频格式检查和转码测试脚本

echo "=== 视频格式检查和转码功能测试 ==="
echo ""

# 检查 ffprobe
echo "1. 检查工具..."
if ! command -v ffprobe &> /dev/null; then
    echo "❌ ffprobe 未安装"
    exit 1
fi
echo "✅ ffprobe 已安装"

if ! command -v ffmpeg &> /dev/null; then
    echo "❌ ffmpeg 未安装"
    exit 1
fi
echo "✅ ffmpeg 已安装"

echo ""
echo "2. 检查当前视频格式..."
VIDEO_DIR="$HOME/.openclaw/workspace/course-ai-helper/data/videos"

for video in "$VIDEO_DIR"/*.mp4; do
    if [ -f "$video" ]; then
        filename=$(basename "$video")
        format=$(ffprobe -v error -show_entries format=format_name -of default=noprint_wrappers=1:nokey=1 "$video" 2>/dev/null)
        
        if [[ "$format" == *"mp4"* ]] || [[ "$format" == *"mov"* ]]; then
            echo "✅ $filename - 格式：$format (兼容)"
        else
            echo "⚠️  $filename - 格式：$format (不兼容，需要转码)"
        fi
    fi
done

echo ""
echo "3. 测试扫描 API..."
curl -s -X POST http://localhost:8000/api/videos/scan \
    -H "Content-Type: application/json" \
    -d '{}' | python3 -m json.tool

echo ""
echo "=== 测试完成 ==="
