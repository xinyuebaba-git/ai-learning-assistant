#!/usr/bin/env python3
"""
重新生成视频总结脚本

用于修复总结生成失败的视频
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.db.base import async_session_maker
from app.services.processor import VideoProcessingService
from sqlalchemy import select, update
from app.models.video import Video, VideoStatus


async def regenerate_summary(video_id: int):
    """重新生成指定视频的总结"""
    async with async_session_maker() as session:
        # 获取视频
        result = await session.execute(select(Video).where(Video.id == video_id))
        video = result.scalar_one_or_none()
        
        if not video:
            print(f"❌ 视频 {video_id} 不存在")
            return False
        
        print(f"📹 处理视频：{video.filename}")
        print(f"   当前状态：{video.status}")
        print(f"   已有字幕：{'✅' if video.has_subtitle else '❌'}")
        print(f"   已有总结：{'✅' if video.has_summary else '❌'}")
        
        # 如果已有总结，先重置状态
        if video.has_summary:
            print(f"⚠️  检测到已有总结，将重置状态...")
            video.has_summary = False
            video.summary_path = None
            video.status = VideoStatus.SUBTITLED
            await session.commit()
            print(f"✓ 状态已重置")
        
        # 创建处理器
        processor = VideoProcessingService(session)
        
        try:
            # 只生成总结（跳过字幕）
            print(f"\n🚀 开始生成总结...")
            await processor._generate_summary(video)
            print(f"✅ 总结生成成功！")
            
            # 尝试创建向量索引
            try:
                await processor._create_embeddings(video)
                print(f"✅ 向量索引创建成功！")
            except Exception as e:
                print(f"⚠️  向量索引创建失败（可忽略）: {e}")
            
            # 更新状态
            video.status = VideoStatus.SUMMARIZED
            video.processed_at = asyncio.get_event_loop().time()
            await session.commit()
            
            print(f"\n🎉 视频 {video_id} 处理完成！")
            return True
            
        except Exception as e:
            print(f"❌ 总结生成失败：{e}")
            video.status = VideoStatus.FAILED
            video.error_message = str(e)
            await session.commit()
            return False


async def main():
    """主函数"""
    print("=" * 60)
    print("🎬 Course AI Helper - 视频总结重新生成工具")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("\n用法：python3 regenerate_summaries.py <video_id>")
        print("示例：python3 regenerate_summaries.py 1")
        print("\n需要处理的视频:")
        print("  视频 1: 桃花源记（状态已修复，需重新生成总结）")
        print("  视频 3: 语法课（未生成总结）")
        sys.exit(1)
    
    video_id = int(sys.argv[1])
    print(f"\n📋 任务：重新生成视频 {video_id} 的总结\n")
    
    success = await regenerate_summary(video_id)
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 任务完成！")
    else:
        print("❌ 任务失败，请查看日志")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
