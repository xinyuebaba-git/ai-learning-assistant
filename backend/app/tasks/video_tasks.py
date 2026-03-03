"""
视频处理 Celery 任务

异步处理视频（生成字幕、总结、向量索引）
"""
from loguru import logger
from datetime import datetime
import asyncio

from app.core.celery_app import celery_app
from app.db.base import async_session_maker
from app.services.processor import VideoProcessingService
from app.models.video import Video, VideoStatus
from sqlalchemy import select


@celery_app.task(bind=True, max_retries=3, acks_late=True)
def process_video_task(self, video_id: int):
    """
    处理视频任务（异步）
    
    Args:
        video_id: 视频 ID
    
    Returns:
        dict: 处理结果
    """
    logger.info(f"🎬 开始处理视频任务：video_id={video_id}")
    
    try:
        # 更新视频状态为处理中
        asyncio.run(_update_video_status(video_id, VideoStatus.SUBTITLING))
        
        # 创建数据库会话
        async def _process():
            async with async_session_maker() as session:
                processor = VideoProcessingService(session)
                result = await processor.process_video(video_id)
                await session.commit()
                return result
        
        # 执行处理
        result = asyncio.run(_process())
        
        logger.info(f"✅ 视频处理完成：video_id={video_id}, result={result}")
        
        return {
            "success": True,
            "video_id": video_id,
            "status": "completed",
            "result": result,
            "completed_at": datetime.utcnow().isoformat(),
        }
        
    except Exception as exc:
        logger.error(f"❌ 视频处理失败：video_id={video_id}, error={exc}")
        
        # 更新视频状态为失败
        try:
            asyncio.run(_update_video_status(video_id, VideoStatus.FAILED, str(exc)))
        except:
            pass
        
        # 重试
        if self.request.retries < self.max_retries:
            logger.warning(f"计划重试：attempt={self.request.retries + 1}/{self.max_retries}")
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        else:
            logger.error(f"达到最大重试次数：video_id={video_id}")
            
            return {
                "success": False,
                "video_id": video_id,
                "status": "failed",
                "error": str(exc),
                "failed_at": datetime.utcnow().isoformat(),
            }


async def _update_video_status(
    video_id: int, 
    status: VideoStatus, 
    error_message: str = None
):
    """更新视频状态"""
    async with async_session_maker() as session:
        result = await session.execute(select(Video).where(Video.id == video_id))
        video = result.scalar_one_or_none()
        
        if video:
            video.status = status
            if error_message:
                video.error_message = error_message
            video.updated_at = datetime.utcnow()
            await session.commit()


@celery_app.task
def get_task_progress(task_id: str):
    """
    获取任务进度
    
    Args:
        task_id: Celery 任务 ID
    
    Returns:
        dict: 任务状态和进度
    """
    from celery.result import AsyncResult
    
    task_result = AsyncResult(task_id, app=celery_app)
    
    return {
        "task_id": task_id,
        "status": task_result.status,
        "ready": task_result.ready(),
        "successful": task_result.successful() if task_result.ready() else None,
        "result": task_result.result if task_result.ready() else None,
    }


@celery_app.task
def cleanup_old_tasks():
    """清理旧任务结果"""
    logger.info("清理旧任务结果...")
    # 这里可以添加清理逻辑
    return "Cleanup completed"
