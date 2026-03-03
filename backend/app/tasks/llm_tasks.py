"""
LLM 内容生成 Celery 任务
"""
from loguru import logger
from datetime import datetime
import asyncio

from app.core.celery_app import celery_app


@celery_app.task(bind=True, max_retries=2)
def summarize_task(self, subtitle_text: str, video_title: str = "", video_id: int = None):
    """
    LLM 内容总结任务
    
    Args:
        subtitle_text: 字幕文本
        video_title: 视频标题
        video_id: 视频 ID（可选）
    
    Returns:
        dict: 总结结果
    """
    logger.info(f"🧠 开始生成总结：video_title={video_title}")
    
    try:
        # 导入 LLM 服务
        from app.services.llm import LLMService
        
        llm_service = LLMService()
        
        # 执行总结
        async def _summarize():
            return await llm_service.summarize(subtitle_text, video_title)
        
        result = asyncio.run(_summarize())
        
        logger.info(f"✅ 总结生成完成：知识点数量={len(result.get('knowledge_points', []))}")
        
        return {
            "success": True,
            "video_id": video_id,
            "summary": result.get("summary", ""),
            "knowledge_points": result.get("knowledge_points", []),
            "token_count": result.get("token_count", 0),
            "completed_at": datetime.utcnow().isoformat(),
        }
        
    except Exception as exc:
        logger.error(f"❌ 总结生成失败：video_title={video_title}, error={exc}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=180)
        else:
            return {
                "success": False,
                "video_id": video_id,
                "error": str(exc),
                "failed_at": datetime.utcnow().isoformat(),
            }


@celery_app.task(bind=True, max_retries=2)
def answer_question_task(self, question: str, context: str):
    """
    LLM 问答任务
    
    Args:
        question: 用户问题
        context: 上下文
    
    Returns:
        str: 回答
    """
    logger.info(f"🤔 回答问题：question={question[:50]}...")
    
    try:
        from app.services.llm import LLMService
        
        llm_service = LLMService()
        
        async def _answer():
            return await llm_service.answer_question(question, context)
        
        answer = asyncio.run(_answer())
        
        logger.info(f"✅ 回答完成")
        
        return {
            "success": True,
            "answer": answer,
            "completed_at": datetime.utcnow().isoformat(),
        }
        
    except Exception as exc:
        logger.error(f"❌ 回答失败：question={question[:50]}, error={exc}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60)
        else:
            return {
                "success": False,
                "error": str(exc),
                "failed_at": datetime.utcnow().isoformat(),
            }
