#!/usr/bin/env python3
"""
知识点生成脚本 - 两阶段处理
1. 理解字幕内容，总结知识点（不带时间戳）
2. 对照字幕上下文，为知识点匹配时间戳（语义匹配）
"""
import sqlite3
import json
import sys
import os

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

DB_PATH = "/Users/nannan/.openclaw/workspace/course-ai-helper/backend/data/course_ai.db"

def load_subtitles(video_id, max_chars=15000):
    """加载视频字幕"""
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

async def stage1_generate_knowledge_points(video_info, subtitles):
    """
    阶段 1：理解字幕内容，总结知识点
    输出知识点列表（不含时间戳）
    """
    from app.services.llm import LLMService
    
    # 构建字幕文本
    subtitle_text = "\n".join([f"[{s['start']:.1f}] {s['text']}" for s in subtitles])
    
    llm = LLMService(backend="alibaba")
    
    system_prompt = """你是一个专业的教育内容分析师。你的任务是深入理解视频内容，总结出关键知识点。

## 输出格式（JSON）
{
  "knowledge_points": [
    {
      "title": "知识点标题（中文，简洁明了）",
      "description": "详细描述（中文，100-200 字）",
      "type": "concept",  // concept/formula/example/key_point
      "keywords": ["关键词 1", "关键词 2"]  // 用于后续时间戳匹配的关键词
    }
  ]
}

## 要求
1. **深入理解**：不要简单提取，要理解内容后总结
2. **知识点类型**：
   - concept: 概念定义
   - formula: 公式定理
   - example: 示例案例
   - key_point: 重点难点
3. **数量**：8-12 个知识点
4. **关键词**：每个知识点提供 2-3 个关键词，用于匹配字幕时间戳
5. **输出**：只输出 JSON，不要其他内容"""

    user_prompt = f"""视频标题：{video_info['title']}

字幕内容:
{subtitle_text[:12000]}

请深入理解以上内容，总结出关键知识点。"""

    print("🤖 阶段 1：正在理解内容并生成知识点...")
    
    try:
        result = await llm.summarize(subtitle_text[:12000], video_info['title'])
        kp_list = result.get('knowledge_points', [])
        
        if not kp_list:
            print("❌ AI 没有返回知识点")
            return None
        
        print(f"✅ 生成了 {len(kp_list)} 个知识点")
        
        # 显示前 3 个
        for i, kp in enumerate(kp_list[:3]):
            print(f"  {i+1}. {kp.get('title', 'Unknown')} - 关键词：{kp.get('keywords', [])}")
        
        return kp_list
        
    except Exception as e:
        print(f"❌ 阶段 1 失败：{e}")
        return None

async def stage2_match_timestamps(video_info, subtitles, knowledge_points):
    """
    阶段 2：为知识点匹配时间戳
    基于关键词和语义，在字幕中找到最相关的时间点
    """
    from app.services.llm import LLMService
    
    llm = LLMService(backend="alibaba")
    
    # 准备字幕数据（简化格式）
    subtitle_data = "\n".join([
        f"{i}: [{s['start']:.1f}-{s['end']:.1f}] {s['text']}" 
        for i, s in enumerate(subtitles[:300])  # 限制条数
    ])
    
    # 准备知识点数据
    kp_data = json.dumps(knowledge_points, ensure_ascii=False, indent=2)
    
    system_prompt = """你是一个时间戳匹配专家。你的任务是为每个知识点找到字幕中最相关的时间点。

## 匹配原则
1. **语义匹配**：不是严格字符匹配，而是语义相近
2. **上下文理解**：考虑前后文，找到知识点被讨论的时间段
3. **最佳匹配**：选择最能代表该知识点的时间点

## 输出格式（JSON）
{
  "timestamped_knowledge_points": [
    {
      "title": "知识点标题",
      "description": "描述",
      "type": "concept",
      "timestamp": 120.5,  // 匹配到的时间戳（秒）
      "matched_subtitle_index": 45,  // 匹配到的字幕索引
      "confidence": "high",  // high/medium/low - 匹配置信度
      "reason": "简要说明匹配理由"
    }
  ]
}

## 输出规则
- 只输出 JSON
- 时间戳单位是秒（浮点数）
- 置信度：high（明确提到）/medium（相关讨论）/low（推断）"""

    user_prompt = f"""字幕内容（索引：[开始 - 结束] 文本）:
{subtitle_data}

知识点列表:
{kp_data}

请为每个知识点匹配最相关的时间戳。"""

    print("🤖 阶段 2：正在匹配时间戳...")
    
    try:
        result = await llm.summarize(subtitle_data, "")
        timestamped_list = result.get('timestamped_knowledge_points', [])
        
        if not timestamped_list:
            print("❌ AI 没有返回带时间戳的知识点")
            return None
        
        print(f"✅ 匹配了 {len(timestamped_list)} 个时间戳")
        
        # 显示匹配结果
        for i, kp in enumerate(timestamped_list[:5]):
            ts = kp.get('timestamp', 0)
            conf = kp.get('confidence', '?')
            print(f"  {i+1}. {kp.get('title', 'Unknown')} - {ts:.1f}秒 (置信度：{conf})")
        
        return timestamped_list
        
    except Exception as e:
        print(f"❌ 阶段 2 失败：{e}")
        return None

def save_knowledge_points(video_id, knowledge_points):
    """保存知识点到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM summaries WHERE video_id = ?", (video_id,))
    row = cursor.fetchone()
    
    if row:
        cursor.execute("""
            UPDATE summaries 
            SET knowledge_points = ?, updated_at = datetime('now')
            WHERE video_id = ?
        """, (json.dumps(knowledge_points, ensure_ascii=False), video_id))
        print(f"✅ 更新了视频 {video_id} 的知识点")
    else:
        # 创建总结记录
        cursor.execute("""
            INSERT INTO summaries (video_id, content, knowledge_points, created_at, updated_at)
            VALUES (?, '', ?, datetime('now'), datetime('now'))
        """, (video_id, json.dumps(knowledge_points, ensure_ascii=False)))
        print(f"✅ 创建了视频 {video_id} 的知识点")
    
    conn.commit()
    conn.close()

async def main(video_id):
    print(f"=========================================")
    print(f"两阶段知识点生成 - 视频 {video_id}")
    print(f"=========================================\n")
    
    # 加载数据
    video_info = load_video_info(video_id)
    if not video_info:
        print(f"❌ 视频 {video_id} 不存在")
        return
    
    print(f"📹 视频：{video_info['title']}\n")
    
    subtitles = load_subtitles(video_id)
    if not subtitles:
        print(f"❌ 视频 {video_id} 没有字幕")
        return
    
    # 阶段 1：生成知识点
    print("\n" + "="*50)
    knowledge_points = await stage1_generate_knowledge_points(video_info, subtitles)
    
    if not knowledge_points:
        print("\n❌ 阶段 1 失败，终止流程")
        return
    
    # 阶段 2：匹配时间戳
    print("\n" + "="*50)
    timestamped_kp = await stage2_match_timestamps(video_info, subtitles, knowledge_points)
    
    if not timestamped_kp:
        print("\n❌ 阶段 2 失败，终止流程")
        return
    
    # 保存结果
    print("\n" + "="*50)
    save_knowledge_points(video_id, timestamped_kp)
    
    print(f"\n=========================================")
    print(f"✅ 知识点生成完成!")
    print(f"  视频：{video_info['title']}")
    print(f"  数量：{len(timestamped_kp)} 个")
    print(f"=========================================")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python3 gen_kp_2stage.py <video_id>")
        print("示例：python3 gen_kp_2stage.py 1")
        sys.exit(1)
    
    video_id = int(sys.argv[1])
    import asyncio
    asyncio.run(main(video_id))
