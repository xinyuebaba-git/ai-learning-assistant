#!/bin/bash

echo "========================================="
echo "知识点时间戳诊断"
echo "========================================="
echo ""

# 测试 1: 检查 API 返回
echo "📋 测试 1: API 返回数据检查"
result=$(curl -s "http://localhost:8000/api/videos/1/summary" 2>/dev/null)

# 检查 knowledge_points 字段类型
kp_type=$(echo "$result" | python3 -c "
import sys, json
d = json.load(sys.stdin)
kp = d.get('knowledge_points', [])
print('string' if isinstance(kp, str) else 'array')
" 2>/dev/null)

echo "知识点数据类型：$kp_type"

if [ "$kp_type" = "string" ]; then
    echo "⚠️  知识点是 JSON 字符串，需要前端解析"
    
    # 解析并检查时间戳
    echo ""
    echo "解析后的知识点:"
    echo "$result" | python3 -c "
import sys, json
d = json.load(sys.stdin)
kp_list = json.loads(d['knowledge_points'])
print(f'总数：{len(kp_list)} 个')
print(f'时间戳范围：{min(k[\"timestamp\"] for k in kp_list):.1f} - {max(k[\"timestamp\"] for k in kp_list):.1f} 秒')
print()
print('前 5 个知识点:')
for i, kp in enumerate(kp_list[:5]):
    ts = kp['timestamp']
    mins = int(ts // 60)
    secs = int(ts % 60)
    valid = '✅' if 0 <= ts <= 600 else '❌'
    print(f'{valid} {i+1}. {kp[\"title\"]} - {mins}:{secs:02d} ({ts}秒)')
" 2>/dev/null
else
    echo "✅ 知识点已经是数组格式"
fi

echo ""
echo "========================================="
echo "诊断完成"
echo "========================================="
