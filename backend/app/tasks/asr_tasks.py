"""
ASR 语音识别 Celery 任务
"""
from loguru import logger
from datetime import datetime

from app.core.celery_app import celery_app


@celery_app.task(bind=True, max_retries=2)
def transcribe_task(self, video_path: str, video_id: int = None):
    """
    ASR 语音识别任务
    
    Args:
        video_path: 视频文件路径
        video_id: 视频 ID（可选）
    
    Returns:
        dict: 转录结果
    """
    logger.info(f"🎤 开始 ASR 转录：video_path={video_path}")
    
    try:
        # 导入 ASR 服务
        from app.services.asr import ASRService
        
        asr_service = ASRService()
        
        # 执行转录
        def _transcribe():
            return asr_service.transcribe(video_path)
        
        subtitle_entries = asyncio.run(_transcribe())
        
        logger.info(f"✅ ASR 转录完成：{len(subtitle_entries)} 条字幕")
        
        return {
            "success": True,
            "video_id": video_id,
            "subtitle_count": len(subtitle_entries),
            "subtitles": [
                {
                    "index": entry.index,
                    "start": entry.start,
                    "end": entry.end,
                    "text": entry.text,
                }
                for entry in subtitle_entries
            ],
            "completed_at": datetime.utcnow().isoformat(),
        }
        
    except Exception as exc:
        logger.error(f"❌ ASR 转录失败：video_path={video_path}, error={exc}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=120)
        else:
            return {
                "success": False,
                "video_id": video_id,
                "error": str(exc),
                "failed_at": datetime.utcnow().isoformat(),
            }


# 需要导入 asyncio
import asyncio
