#!/usr/bin/env python3
"""
知识点重新生成脚本 - 通过后端 API 调用
"""
import requests
import json
import sys

API_BASE = "http://localhost:8000"

def regenerate_kp(video_id):
    """重新生成知识点"""
    print(f"=========================================")
    print(f"重新生成视频 {video_id} 的知识点")
    print(f"=========================================\n")
    
    # 调用后端处理接口
    url = f"{API_BASE}/api/videos/{video_id}/process"
    
    print(f"📡 发送请求：POST {url}")
    
    try:
        response = requests.post(url, json={})
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 处理任务已启动")
            print(f"   任务 ID: {result.get('task_id', 'N/A')}")
            print(f"   消息：{result.get('message', '')}")
            print(f"\n📝 处理完成后，知识点将自动更新")
            print(f"   可以通过 {API_BASE}/api/videos/{video_id} 查看结果")
        else:
            print(f"❌ 请求失败：HTTP {response.status_code}")
            print(f"   响应：{response.text[:200]}")
    
    except Exception as e:
        print(f"❌ 请求异常：{e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python3 regen_kp_api.py <video_id>")
        print("示例：python3 regen_kp_api.py 1")
        sys.exit(1)
    
    video_id = int(sys.argv[1])
    regenerate_kp(video_id)
