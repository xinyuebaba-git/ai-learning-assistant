from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from pathlib import Path
from datetime import datetime
import os
import re
import aiofiles

# Celery 导入
from app.core.celery_app import celery_app

from ..db.base import get_db
from ..models.video import Video, VideoStatus
from ..models.user import User
from ..models.favorite import UserFavorite
from ..api.auth import get_current_user_dependency


router = APIRouter()


# ============ Pydantic 模型 ============

from datetime import datetime
from pydantic import BaseModel, field_validator

class VideoResponse(BaseModel):
    """视频响应"""
    id: int
    filename: str
    title: str | None = None
    duration: float | None = None
    file_size: int | None = None
    status: str
    has_subtitle: bool
    has_summary: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class VideoDetailResponse(VideoResponse):
    """视频详情响应"""
    filepath: str
    description: str | None = None
    subtitle_language: str | None = None
    processed_at: datetime | None = None


class ScanRequest(BaseModel):
    """扫描视频请求"""
    directory: Optional[str] = None  # 指定目录，None 则扫描默认视频目录


class FavoriteToggleResponse(BaseModel):
    """收藏切换响应"""
    is_favorited: bool
    message: str


# ============ API 路由 ============

@router.get("", response_model=List[VideoResponse])
async def list_videos(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status_filter: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """获取视频列表"""
    query = select(Video)
    
    # 状态过滤
    if status_filter:
        query = query.where(Video.status == status_filter)
    
    # 搜索过滤
    if search:
        query = query.where(Video.filename.ilike(f"%{search}%"))
    
    # 排序
    query = query.order_by(Video.created_at.desc())
    
    # 分页
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    videos = result.scalars().all()
    
    return videos


# ============ 视频流 API ============

from fastapi.responses import FileResponse, StreamingResponse
from starlette.responses import Response
import aiofiles

@router.get("/{video_id}/stream")
async def stream_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_dependency)
):
    """视频流式传输 - 支持 Range 请求"""
    from fastapi import Request
    
    # 获取视频信息
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 检查文件是否存在
    video_path = Path(video.filepath)
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="视频文件不存在")
    
    # 获取文件大小
    file_size = video_path.stat().st_size
    
    # 使用 FileResponse 自动处理 Range 请求
    return FileResponse(
        str(video_path),
        media_type='video/mp4',
        filename=video.filename,
        headers={
            'Accept-Ranges': 'bytes',
            'Content-Length': str(file_size),
        },
    )


@router.get("/{video_id}", response_model=VideoDetailResponse)
async def get_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """获取视频详情"""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    return video


@router.post("/scan")
async def scan_videos(
    request: ScanRequest = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """扫描视频文件"""
    from ..core.config import settings
    
    # 确定扫描目录
    scan_dir = Path(request.directory) if request and request.directory else Path(settings.VIDEO_DIR)
    
    if not scan_dir.exists():
        raise HTTPException(status_code=400, detail=f"目录不存在：{scan_dir}")
    
    # 支持的视频格式
    video_extensions = {".mp4", ".mov", ".mkv", ".avi", ".m4v", ".webm", ".flv", ".wmv"}
    
    # 扫描文件
    scanned_count = 0
    new_count = 0
    
    for ext in video_extensions:
        for filepath in scan_dir.rglob(f"*{ext}"):
            scanned_count += 1
            
            # 检查是否已存在
            result = await db.execute(
                select(Video).where(Video.filepath == str(filepath))
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                # 创建新视频记录
                video = Video(
                    filename=filepath.name,
                    filepath=str(filepath),
                    title=filepath.stem,  # 默认使用文件名作为标题
                    file_size=filepath.stat().st_size,
                    status=VideoStatus.SCANNED,
                    has_subtitle=False,
                    has_summary=False,
                )
                db.add(video)
                new_count += 1
    
    await db.commit()
    
    return {
        "message": "扫描完成",
        "scanned_count": scanned_count,
        "new_count": new_count,
    }




@router.post("/{video_id}/favorite")
async def toggle_favorite(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """切换收藏状态"""
    # 检查视频是否存在
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 检查是否已收藏
    result = await db.execute(
        select(UserFavorite).where(
            UserFavorite.user_id == current_user.id,
            UserFavorite.video_id == video_id
        )
    )
    favorite = result.scalar_one_or_none()
    
    if favorite:
        # 取消收藏
        await db.delete(favorite)
        await db.commit()
        return FavoriteToggleResponse(is_favorited=False, message="已取消收藏")
    else:
        # 添加收藏
        favorite = UserFavorite(user_id=current_user.id, video_id=video_id)
        db.add(favorite)
        await db.commit()
        return FavoriteToggleResponse(is_favorited=True, message="已加入收藏")


@router.get("/{video_id}/subtitle")
async def get_subtitle(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """获取视频字幕"""
    from ..models.subtitle import Subtitle
    
    # 检查视频是否存在
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    if not video.has_subtitle:
        raise HTTPException(status_code=404, detail="该视频暂无字幕")
    
    # 获取字幕条目
    result = await db.execute(
        select(Subtitle)
        .where(Subtitle.video_id == video_id)
        .order_by(Subtitle.start)
    )
    subtitles = result.scalars().all()
    
    return {
        "video_id": video_id,
        "filename": video.filename,
        "language": video.subtitle_language,
        "subtitles": [sub.to_dict() for sub in subtitles],
    }


@router.get("/{video_id}/summary")
async def get_summary(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """获取视频总结"""
    from ..models.summary import Summary
    
    # 检查视频是否存在
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    if not video.has_summary:
        raise HTTPException(status_code=404, detail="该视频暂无总结")
    
    # 获取总结
    result = await db.execute(select(Summary).where(Summary.video_id == video_id))
    summary = result.scalar_one_or_none()
    
    if not summary:
        raise HTTPException(status_code=404, detail="总结不存在")
    
    return {
        "video_id": video_id,
        "content": summary.content,
        "knowledge_points": summary.knowledge_points,
        "model": summary.model_name,
        "created_at": summary.created_at,
    }


@router.post("/{video_id}/process")
async def process_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """处理视频（异步任务队列）"""
    from app.tasks.video_tasks import process_video_task
    
    # 检查视频是否存在
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 检查是否已处理
    if video.status == VideoStatus.SUMMARIZED:
        return {
            "message": "视频已处理完成",
            "status": video.status,
        }
    
    # 更新状态为处理中
    video.status = VideoStatus.SUBTITLING
    video.updated_at = datetime.utcnow()
    await db.commit()
    
    # 启动 Celery 异步任务
    task = process_video_task.delay(video_id)
    
    logger.info(f"🚀 视频处理任务已启动：video_id={video_id}, task_id={task.id}")
    
    return {
        "message": "视频处理已启动（异步）",
        "video_id": video_id,
        "task_id": task.id,
        "status": "queued",
        "check_status_url": f"/api/videos/{video_id}/process/status",
    }


@router.get("/{video_id}/process/status")
async def get_process_status(
    video_id: int,
    task_id: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """获取视频处理进度"""
    from app.tasks.video_tasks import get_task_progress
    from celery.result import AsyncResult
    
    # 检查视频是否存在
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 获取视频当前状态
    status_info = {
        "video_id": video_id,
        "video_status": video.status,
        "has_subtitle": video.has_subtitle,
        "has_summary": video.has_summary,
        "error_message": video.error_message,
        "processed_at": video.processed_at,
    }
    
    # 如果有 task_id，获取 Celery 任务状态
    if task_id:
        task_result = AsyncResult(task_id, app=celery_app)
        status_info["task"] = {
            "task_id": task_id,
            "status": task_result.status,
            "ready": task_result.ready(),
        }
    
    return status_info


from fastapi import BackgroundTasks


