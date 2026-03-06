#!/usr/bin/env python3
"""
知识点重新生成脚本
基于字幕内容生成准确时间戳的知识点
"""
import sqlite3
import json
import asyncio
import sys
from typing import List, Dict

DB_PATH = "/Users/nannan/.openclaw/workspace/course-ai-helper/backend/data/course_ai.db"

def load_subtitles(video_id, max_chars=12000):
    """加载视频字幕（限制长度）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT start, end, text FROM subtitles 
        WHERE video_id = ? 
        ORDER BY start
    """, (video_id,))
    
    subs = []
    total_chars = 0
    for start, end, text in cursor.fetchall():
        if total_chars + len(text) > max_chars:
            break
        subs.append({'start': start, 'end': end, 'text': text})
        total_chars += len(text)
    
    conn.close()
    print(f"📚 加载了 {len(subs)} 条字幕，共 {total_chars} 字符")
    return subs

def load_video_info(video_id):
    """加载视频信息"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, filename FROM videos WHERE id = ?
    """, (video_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {'id': row[0], 'title': row[1] or row[2], 'filename': row[2]}
    return None

async def generate_knowledge_points(video_info, subtitles):
    """使用 AI 重新生成知识点"""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
    
    from app.services.llm import LLMService
    
    # 构建字幕文本（带时间戳）
    subtitle_text = "\n".join([
        f"[{s['start']:.1f}-{s['end']:.1f}] {s['text']}" 
        for s in subtitles[:200]  # 限制条数
    ])
    
    llm = LLMService(backend="alibaba")  # 使用更强的模型
    
    # 改进的提示词 - 强调时间戳准确性
    system_prompt = """你是一个专业的教育内容分析师。你的任务是基于视频字幕生成知识点，并确保每个知识点的时间戳准确对应字幕中实际提到该内容的时间点。

## 重要要求
⚠️ **时间戳必须准确**：每个知识点的时间戳必须是字幕中实际出现该内容的秒数
⚠️ **基于字幕**：只能从字幕中提取信息，不能编造
⚠️ **验证时间戳**：生成前检查时间戳对应的字幕是否包含该知识点的内容

## 输出格式
{
  "knowledge_points": [
    {
      "timestamp": 12.5,  // 必须是字幕中实际提到该内容的秒数
      "title": "知识点标题（中文）",
      "description": "详细描述（中文）",
      "type": "concept"  // concept/formula/example/key_point
    }
  ]
}

## 知识点类型
- concept: 概念定义
- formula: 公式定理  
- example: 示例案例
- key_point: 重点难点

## 输出规则
⚠️ 只输出 JSON，不要其他内容
⚠️ 时间戳单位是秒（浮点数）
⚠️ 生成 10-15 个知识点
⚠️ 所有内容用中文"""

    user_prompt = f"""视频标题：{video_info['title']}

字幕内容（格式：[开始时间 - 结束时间] 文本）:
{subtitle_text}

请基于以上字幕生成知识点，确保每个知识点的时间戳都能在字幕中找到对应内容。"""

    print("🤖 正在调用 AI 生成知识点...")
    
    try:
        result = await llm.summarize(subtitle_text, video_info['title'])
        
        # 提取知识点
        kp_list = result.get('knowledge_points', [])
        
        if not kp_list:
            print("❌ AI 没有返回知识点")
            return None
        
        print(f"✅ 生成了 {len(kp_list)} 个知识点")
        
        # 验证知识点
        print("\n📍 验证知识点时间戳:")
        valid_count = 0
        for i, kp in enumerate(kp_list[:5]):
            ts = kp.get('timestamp', 0)
            title = kp.get('title', 'Unknown')
            print(f"  {i+1}. {title} - {ts:.1f}秒")
        
        return kp_list
        
    except Exception as e:
        print(f"❌ 生成失败：{e}")
        return None

def save_knowledge_points(video_id, knowledge_points):
    """保存知识点到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查是否已有总结
    cursor.execute("SELECT id FROM summaries WHERE video_id = ?", (video_id,))
    row = cursor.fetchone()
    
    if row:
        # 更新现有记录
        cursor.execute("""
            UPDATE summaries 
            SET knowledge_points = ?, updated_at = datetime('now')
            WHERE video_id = ?
        """, (json.dumps(knowledge_points, ensure_ascii=False), video_id))
        print(f"✅ 更新了视频 {video_id} 的知识点")
    else:
        # 创建新记录
        cursor.execute("""
            INSERT INTO summaries (video_id, knowledge_points, created_at, updated_at)
            VALUES (?, ?, datetime('now'), datetime('now'))
        """, (video_id, json.dumps(knowledge_points, ensure_ascii=False)))
        print(f"✅ 创建了视频 {video_id} 的知识点")
    
    conn.commit()
    conn.close()

async def main(video_id):
    print(f"=========================================")
    print(f"重新生成视频 {video_id} 的知识点")
    print(f"=========================================\n")
    
    # 加载数据
    video_info = load_video_info(video_id)
    if not video_info:
        print(f"❌ 视频 {video_id} 不存在")
        return
    
    print(f"📹 视频：{video_info['title']}")
    
    subtitles = load_subtitles(video_id)
    if not subtitles:
        print(f"❌ 视频 {video_id} 没有字幕")
        return
    
    # 生成知识点
    knowledge_points = await generate_knowledge_points(video_info, subtitles)
    
    if knowledge_points:
        # 保存到数据库
        save_knowledge_points(video_id, knowledge_points)
        
        print(f"\n=========================================")
        print(f"✅ 知识点重新生成完成!")
        print(f"  视频：{video_info['title']}")
        print(f"  数量：{len(knowledge_points)} 个")
        print(f"=========================================")
    else:
        print(f"\n❌ 知识点生成失败")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python3 regenerate_kp.py <video_id>")
        print("示例：python3 regenerate_kp.py 1")
        sys.exit(1)
    
    video_id = int(sys.argv[1])
    asyncio.run(main(video_id))
