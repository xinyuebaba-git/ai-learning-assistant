#!/usr/bin/env python3
"""
知识点时间戳修复脚本
基于字幕内容重新匹配知识点的时间戳
"""
import sqlite3
import json
import sys

DB_PATH = "/Users/nannan/.openclaw/workspace/course-ai-helper/backend/data/course_ai.db"

def load_subtitles(video_id):
    """加载视频字幕"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT start, end, text FROM subtitles 
        WHERE video_id = ? 
        ORDER BY start
    """, (video_id,))
    subs = cursor.fetchall()
    conn.close()
    return subs

def load_knowledge_points(video_id):
    """加载现有知识点"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT knowledge_points FROM summaries 
        WHERE video_id = ?
    """, (video_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row and row[0]:
        kp_data = row[0]
        # 如果是字符串，解析 JSON
        if isinstance(kp_data, str):
            try:
                return json.loads(kp_data)
            except json.JSONDecodeError as e:
                print(f"❌ JSON 解析失败：{e}")
                return []
        elif isinstance(kp_data, list):
            return kp_data
        else:
            print(f"⚠️ 未知格式：{type(kp_data)}")
            return []
    return []

def match_timestamp(kp_title, kp_desc, subtitles):
    """基于关键词匹配最相关的字幕时间戳"""
    # 提取知识点中的关键词
    keywords = []
    for text in [kp_title, kp_desc or '']:
        # 简单分词（按标点符号）
        words = text.replace(',', ' ').replace('，', ' ').replace('。', ' ').split()
        keywords.extend([w for w in words if len(w) > 1])
    
    # 去重
    keywords = list(set(keywords))[:10]  # 只取前 10 个关键词
    
    # 查找包含关键词的字幕
    matches = []
    for start, end, text in subtitles:
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            matches.append((start, end, text, score))
    
    # 按匹配度排序
    matches.sort(key=lambda x: x[3], reverse=True)
    
    if matches:
        # 返回最佳匹配的时间戳
        best = matches[0]
        return best[0], best[1], best[2], len(keywords)
    
    # 没有匹配，返回原时间戳
    return None, None, None, 0

def fix_knowledge_points(video_id):
    """修复知识点时间戳"""
    print(f"📍 修复视频 {video_id} 的知识点时间戳")
    
    subtitles = load_subtitles(video_id)
    knowledge_points = load_knowledge_points(video_id)
    
    if not knowledge_points:
        print(f"❌ 视频 {video_id} 没有知识点")
        return
    
    print(f"📊 加载了 {len(subtitles)} 条字幕，{len(knowledge_points)} 个知识点")
    print()
    
    fixed_count = 0
    not_found_count = 0
    
    for i, kp in enumerate(knowledge_points):
        # 确保 kp 是字典
        if isinstance(kp, str):
            # 尝试解析字符串
            try:
                kp = json.loads(kp)
            except:
                print(f"⚠️  跳过第 {i+1} 个知识点（无法解析的字符串）")
                continue
        
        if not isinstance(kp, dict):
            print(f"⚠️  跳过第 {i+1} 个知识点（非字典格式：{type(kp)})")
            continue
        
        old_ts = kp.get('timestamp', 0)
        
        # 尝试匹配新的时间戳
        new_start, new_end, matched_text, score = match_timestamp(
            kp['title'], 
            kp.get('description', ''), 
            subtitles
        )
        
        if new_start is not None:
            # 找到匹配
            kp['timestamp'] = new_start
            kp['matched_subtitle'] = matched_text
            kp['timestamp_accuracy'] = 'matched'
            fixed_count += 1
            print(f"✅ {i+1}. {kp['title']}")
            print(f"   旧时间：{old_ts:.1f} 秒 → 新时间：{new_start:.1f} 秒 ({int(new_start//60)}:{int(new_start%60):02d})")
            print(f"   匹配字幕：{matched_text[:50]}...")
        else:
            # 未找到匹配，保留原时间戳但标记
            kp['timestamp_accuracy'] = 'estimated'
            not_found_count += 1
            print(f"⚠️  {i+1}. {kp['title']}")
            print(f"   时间：{old_ts:.1f} 秒 (未找到匹配，保留估算值)")
        
        print()
    
    # 保存修复后的知识点
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE summaries 
        SET knowledge_points = ?
        WHERE video_id = ?
    """, (json.dumps(knowledge_points, ensure_ascii=False), video_id))
    conn.commit()
    conn.close()
    
    print(f"=========================================")
    print(f"修复完成!")
    print(f"  成功匹配：{fixed_count} 个")
    print(f"  未找到匹配：{not_found_count} 个")
    print(f"  总计：{len(knowledge_points)} 个")
    print(f"=========================================")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python3 fix_kp_timestamps.py <video_id>")
        print("示例：python3 fix_kp_timestamps.py 1")
        sys.exit(1)
    
    video_id = int(sys.argv[1])
    fix_knowledge_points(video_id)
