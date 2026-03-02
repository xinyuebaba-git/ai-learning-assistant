"""
视频处理服务 - 后台任务处理

负责调用 ASR 生成字幕、调用 LLM 生成总结
"""
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.video import Video, VideoStatus
from ..models.subtitle import Subtitle
from ..models.summary import Summary
from ..services.asr import ASRService, get_asr_service
from ..services.llm import LLMService, get_llm_service
from ..services.search import get_search_service


class VideoProcessingService:
    """视频处理服务"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.asr_service = get_asr_service()
        self.llm_service = get_llm_service()
        self.search_service = get_search_service()
    
    async def process_video(self, video_id: int) -> dict:
        """
        处理视频：生成字幕 + 生成总结 + 创建向量索引
        
        Args:
            video_id: 视频 ID
        
        Returns:
            处理结果
        """
        # 获取视频
        result = await self.db.execute(select(Video).where(Video.id == video_id))
        video = result.scalar_one_or_none()
        
        if not video:
            raise ValueError(f"视频不存在：{video_id}")
        
        logger.info(f"开始处理视频：{video.filename} (ID: {video_id})")
        
        try:
            # 步骤 1: 生成字幕
            await self._generate_subtitles(video)
            
            # 步骤 2: 生成总结
            await self._generate_summary(video)
            
            # 步骤 3: 创建向量索引
            await self._create_embeddings(video)
            
            # 更新状态
            video.status = VideoStatus.SUMMARIZED
            video.processed_at = datetime.utcnow()
            await self.db.commit()
            
            logger.info(f"✅ 视频处理完成：{video.filename}")
            
            return {
                "success": True,
                "video_id": video_id,
                "subtitle_count": len(video.subtitles),
                "knowledge_points": len(video.summary.knowledge_points) if video.summary else 0,
            }
            
        except Exception as e:
            logger.error(f"❌ 视频处理失败：{video.filename}, 错误：{e}")
            video.status = VideoStatus.FAILED
            video.error_message = str(e)
            await self.db.commit()
            
            return {
                "success": False,
                "video_id": video_id,
                "error": str(e),
            }
    
    async def _generate_subtitles(self, video: Video):
        """生成字幕"""
        logger.info(f"步骤 1/3: 生成字幕 - {video.filename}")
        video.status = VideoStatus.SUBTITLING
        await self.db.commit()
        
        # 检查是否已有字幕文件
        if video.has_subtitle and video.subtitle_path:
            logger.info(f"字幕已存在，跳过：{video.subtitle_path}")
            return
        
        # 调用 ASR 服务
        subtitle_entries = await self.asr_service.transcribe(
            video.filepath,
            progress_callback=lambda p: logger.info(f"转录进度：{p*100:.1f}%")
        )
        
        # 保存字幕到数据库
        for entry in subtitle_entries:
            subtitle = Subtitle(
                video_id=video.id,
                index=entry.index,
                start=entry.start,
                end=entry.end,
                text=entry.text,
            )
            self.db.add(subtitle)
        
        # 保存 SRT 文件
        from ..core.config import settings
        srt_path = Path(settings.SUBTITLE_DIR) / f"{video.id}.zh-CN.srt"
        self.asr_service.save_srt(subtitle_entries, str(srt_path))
        
        # 更新视频状态
        video.has_subtitle = True
        video.subtitle_path = str(srt_path)
        video.subtitle_language = "zh-CN"
        video.subtitle_source = "asr"
        
        await self.db.commit()
        logger.info(f"✅ 字幕生成完成：{len(subtitle_entries)} 条")
    
    async def _generate_summary(self, video: Video):
        """生成内容总结"""
        logger.info(f"步骤 2/3: 生成总结 - {video.filename}")
        video.status = VideoStatus.SUMMARIZING
        await self.db.commit()
        
        # 检查是否已有总结
        if video.has_summary and video.summary_path:
            logger.info(f"总结已存在，跳过：{video.summary_path}")
            return
        
        # 获取所有字幕文本
        result = await self.db.execute(
            select(Subtitle)
            .where(Subtitle.video_id == video.id)
            .order_by(Subtitle.start)
        )
        subtitles = result.scalars().all()
        
        if not subtitles:
            raise ValueError("没有字幕内容，无法生成总结")
        
        # 拼接字幕文本
        subtitle_text = "\n".join([sub.text for sub in subtitles])
        
        # 调用 LLM 服务生成总结
        summary_result = await self.llm_service.summarize(
            subtitle_text=subtitle_text,
            video_title=video.title or video.filename,
        )
        
        # 保存总结
        summary = Summary(
            video_id=video.id,
            content=summary_result["summary"],
            knowledge_points=summary_result["knowledge_points"],
            model_backend=self.llm_service.backend,
            model_name=self.llm_service.model,
            token_count=summary_result["token_count"],
        )
        self.db.add(summary)
        
        # 更新视频状态
        video.has_summary = True
        video.summary_path = f"summary_{video.id}.json"
        
        await self.db.commit()
        logger.info(f"✅ 总结生成完成，知识点：{len(summary_result['knowledge_points'])} 个")
    
    async def _create_embeddings(self, video: Video):
        """创建向量索引"""
        logger.info(f"步骤 3/3: 创建向量索引 - {video.filename}")
        
        try:
            # 获取字幕
            result = await self.db.execute(
                select(Subtitle)
                .where(Subtitle.video_id == video.id)
                .order_by(Subtitle.start)
            )
            subtitles = result.scalars().all()
            
            # 准备字幕文本和元数据
            subtitle_texts = []
            subtitle_metadatas = []
            
            for sub in subtitles:
                # 只处理有实际内容的字幕
                if sub.text.strip():
                    subtitle_texts.append(sub.text)
                    subtitle_metadatas.append({
                        "type": "subtitle",
                        "start": sub.start,
                        "end": sub.end,
                    })
            
            # 添加到向量索引
            if subtitle_texts:
                await self.search_service.add_embeddings(
                    video_id=video.id,
                    texts=subtitle_texts,
                    metadatas=subtitle_metadatas,
                )
            
            # 添加总结到向量索引
            if video.summary:
                await self.search_service.add_embeddings(
                    video_id=video.id,
                    texts=[video.summary.content],
                    metadatas=[{"type": "summary"}],
                )
            
            logger.info(f"✅ 向量索引创建完成：{len(subtitle_texts)} 条字幕 + 1 条总结")
        except Exception as e:
            logger.warning(f"⚠️ 向量索引创建失败（已跳过）: {e}")
            logger.warning(f"提示：Python 3.14 与 ChromaDB 存在兼容性问题，可暂时忽略此错误")


async def process_video_task(video_id: int, db_session: AsyncSession):
    """视频处理任务入口（用于后台任务队列）"""
    processor = VideoProcessingService(db_session)
    return await processor.process_video(video_id)
