#!/usr/bin/env python3
"""
基于字幕生成简单知识点
"""
import sqlite3
import json
import sys

DB_PATH = "/Users/nannan/.openclaw/workspace/course-ai-helper/backend/data/course_ai.db"

def generate_simple_kp(video_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取视频信息
    cursor.execute("SELECT title FROM videos WHERE id = ?", (video_id,))
    title = cursor.fetchone()[0]
    
    # 获取字幕（按时间段分组）
    cursor.execute("""
        SELECT start, text FROM subtitles 
        WHERE video_id = ? AND start < 600
        ORDER BY start
    """, (video_id,))
    
    subtitles = cursor.fetchall()
    
    # 简单规则：每 60 秒提取一个知识点
    knowledge_points = []
    current_minute = -1
    
    for start, text in subtitles:
        minute = int(start // 60)
        if minute > current_minute and len(text) > 10:
            current_minute = minute
            knowledge_points.append({
                "timestamp": float(start),
                "title": f"第{minute + 1}分钟内容",
                "description": text[:100],
                "type": "key_point"
            })
            
            if len(knowledge_points) >= 10:
                break
    
    # 保存到数据库
    cursor.execute("""
        UPDATE summaries 
        SET knowledge_points = ?, updated_at = datetime('now')
        WHERE video_id = ?
    """, (json.dumps(knowledge_points, ensure_ascii=False), video_id))
    
    conn.commit()
    conn.close()
    
    print(f"✅ 生成了 {len(knowledge_points)} 个知识点")
    for i, kp in enumerate(knowledge_points):
        ts = kp['timestamp']
        print(f"  {i+1}. {kp['title']} - {int(ts//60)}:{int(ts%60):02d} ({ts}秒)")

if __name__ == "__main__":
    video_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    generate_simple_kp(video_id)
