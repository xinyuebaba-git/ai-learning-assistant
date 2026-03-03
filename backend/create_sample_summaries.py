#!/usr/bin/env python3
"""
创建示例总结脚本

用于测试和演示目的，生成示例总结数据
"""
import sqlite3
import json
from datetime import datetime

conn = sqlite3.connect('data/course_ai.db')
cursor = conn.cursor()

# 视频 1: 桃花源记
video_1_summary = {
    "summary": "本课程详细讲解了陶渊明的《桃花源记》。文章通过武陵渔人的视角，描绘了一个与世隔绝的理想社会。课程首先介绍了作者陶渊明的生平和创作背景，然后逐段分析了文章内容，包括渔人发现桃花源的经过、桃花源中的生活景象、以及最终无法再寻桃花源的结局。文章表达了作者对理想社会的向往和对现实社会的不满。课程还重点讲解了文中的文言词汇和句式，如'仿佛'、'豁然开朗'等，帮助学生理解古文表达方式。",
    "knowledge_points": [
        {"timestamp": 15.0, "title": "作者介绍", "description": "陶渊明，东晋诗人，字元亮，号五柳先生", "type": "concept"},
        {"timestamp": 45.0, "title": "创作背景", "description": "东晋末年社会动荡，作者向往田园生活", "type": "key_point"},
        {"timestamp": 120.5, "title": "豁然开朗", "description": "形容由狭窄幽暗突然变得开阔明亮，比喻突然领悟", "type": "concept"},
        {"timestamp": 180.0, "title": "桃花源景象", "description": "土地平旷，屋舍俨然，有良田美池桑竹之属", "type": "example"},
        {"timestamp": 240.0, "title": "世外桃源", "description": "比喻理想中的美好世界", "type": "concept"},
        {"timestamp": 300.0, "title": "文言词汇：仿佛", "description": "隐隐约约，形容看得不真切", "type": "concept"},
        {"timestamp": 360.0, "title": "文章主旨", "description": "表达对理想社会的向往和对现实的不满", "type": "key_point"},
        {"timestamp": 420.0, "title": "写作手法", "description": "虚实结合，以渔人经历为线索", "type": "key_point"}
    ]
}

# 视频 3: 语法课
video_3_summary = {
    "summary": "本课程讲解了英语语法中的状语从句易错点、词汇辨析以及篇章类阅读技巧。课程首先分析了状语从句的常见错误类型，包括时态不一致、连词误用等问题，并通过大量例句进行说明。接着讲解了重点词汇的用法和辨析，帮助学生准确理解和运用。最后介绍了篇章类阅读中的填表题解题技巧，包括如何快速定位信息、如何准确概括段落大意等。课程内容实用，讲解清晰，适合中学生英语学习。",
    "knowledge_points": [
        {"timestamp": 30.0, "title": "状语从句类型", "description": "时间、地点、原因、结果、条件等状语从句", "type": "concept"},
        {"timestamp": 90.0, "title": "时态一致原则", "description": "主句和从句时态要保持逻辑一致", "type": "key_point"},
        {"timestamp": 150.0, "title": "连词辨析", "description": "because/since/as 的区别", "type": "concept"},
        {"timestamp": 210.0, "title": "词汇：affect vs effect", "description": "affect 是动词，effect 是名词", "type": "concept"},
        {"timestamp": 270.0, "title": "阅读填表技巧", "description": "先读表格，再读文章，定位关键信息", "type": "key_point"},
        {"timestamp": 330.0, "title": "段落大意概括", "description": "找主题句，通常是段首或段尾", "type": "formula"},
        {"timestamp": 390.0, "title": "同义词替换", "description": "表格中常用原文的同义词", "type": "example"},
        {"timestamp": 450.0, "title": "检查答案", "description": "检查语法、拼写和字数要求", "type": "key_point"}
    ]
}

summaries = [
    (1, video_1_summary),
    (3, video_3_summary)
]

print("=" * 60)
print("📝 创建示例总结")
print("=" * 60)

for video_id, summary_data in summaries:
    print(f"\n处理视频 {video_id}...")
    
    # 插入总结
    cursor.execute("""
        INSERT INTO summaries (video_id, content, knowledge_points, model_backend, model_name, token_count, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        video_id,
        summary_data["summary"],
        json.dumps(summary_data["knowledge_points"], ensure_ascii=False),
        "manual",
        "sample",
        0,
        datetime.utcnow(),
        datetime.utcnow()
    ))
    
    # 更新视频状态
    cursor.execute("""
        UPDATE videos 
        SET has_summary = 1, 
            summary_path = ?,
            status = 'SUMMARIZED',
            processed_at = ?
        WHERE id = ?
    """, (f"summary_{video_id}.json", datetime.utcnow(), video_id))
    
    print(f"✓ 视频 {video_id} 总结已创建，知识点数量：{len(summary_data['knowledge_points'])}")

conn.commit()

print("\n" + "=" * 60)
print("✅ 示例总结创建完成！")
print("=" * 60)

print("\n=== 当前视频状态 ===")
cursor.execute('SELECT id, filename, status, has_summary FROM videos')
for row in cursor.fetchall():
    status = '✅' if row[2] == 'SUMMARIZED' else '⏳'
    print(f'{status} 视频 {row[0]}: {row[1][:40]} - 总结:{row[3]}')

conn.close()
