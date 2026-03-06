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
import json
import logging

# Celery 导入
from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)

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
    # current_user: User = Depends(get_current_user_dependency)
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
from urllib.parse import quote
@router.get("/{video_id}/play")
async def play_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
):
    """视频播放 - 不需要认证"""
    # 获取视频信息
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 检查文件是否存在
    video_path = Path(video.filepath)
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="视频文件不存在")
    
    # 使用 FileResponse 自动处理 Range 请求
    # 设置正确的响应头 - 中文文件名需要 URL 编码
    filename_encoded = quote(video.filename)
    headers = {
        'Accept-Ranges': 'bytes',
        'Content-Type': 'video/mp4',
        'Content-Disposition': f"inline; filename*=UTF-8''{filename_encoded}",
        'Cache-Control': 'public, max-age=3600',
    }
    
    return FileResponse(
        str(video_path),
        media_type='video/mp4',
        headers=headers,
    )


@router.get("/{video_id}/stream")
async def stream_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
):
    """视频流式传输 - 支持 Range 请求（不需要认证）"""
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
    # current_user: User = Depends(get_current_user_dependency)
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
    # current_user: User = Depends(get_current_user_dependency)
):
    """扫描视频文件，并检查格式兼容性"""
    from ..core.config import settings
    import subprocess
    import json
    
    # 确定扫描目录
    scan_dir = Path(request.directory) if request and request.directory else Path(settings.VIDEO_DIR)
    
    if not scan_dir.exists():
        raise HTTPException(status_code=400, detail=f"目录不存在：{scan_dir}")
    
    # 支持的视频格式
    video_extensions = {".mp4", ".mov", ".mkv", ".avi", ".m4v", ".webm", ".flv", ".wmv"}
    
    # 浏览器兼容的 MP4 容器格式
    COMPATIBLE_FORMATS = {"mov", "mp4", "m4a", "3gp", "3g2", "mj2"}
    
    # 扫描文件
    scanned_count = 0
    new_count = 0
    transcoded_count = 0
    failed_count = 0
    
    def check_video_format(filepath: Path) -> tuple[bool, str | None]:
        """检查视频格式是否浏览器兼容，返回 (是否兼容，容器格式)"""
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=format_name", "-of", "json", str(filepath)],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                return False, None
            
            data = json.loads(result.stdout)
            format_name = data.get("format", {}).get("format_name", "")
            
            # 检查是否为兼容的格式
            is_compatible = any(f in format_name for f in COMPATIBLE_FORMATS)
            return is_compatible, format_name
        except Exception as e:
            print(f"检查视频格式失败 {filepath}: {e}")
            return False, None
    
    def transcode_video(filepath: Path) -> bool:
        """转码视频为标准 MP4 格式"""
        backup_path = filepath.with_suffix(filepath.suffix + ".backup")
        temp_path = filepath.with_suffix(filepath.suffix + ".transcoding.mp4")
        
        try:
            # 备份原文件
            import shutil
            shutil.copy2(filepath, backup_path)
            print(f"已备份原文件：{backup_path}")
            
            # 转码命令
            cmd = [
                "ffmpeg", "-y",
                "-i", str(filepath),
                "-c:v", "libx264",
                "-c:a", "aac",
                "-movflags", "+faststart",
                str(temp_path)
            ]
            
            print(f"开始转码：{filepath.name}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                print(f"转码失败：{filepath.name}")
                print(result.stderr)
                # 恢复备份
                if backup_path.exists():
                    shutil.move(backup_path, filepath)
                return False
            
            # 验证转码后的文件
            is_ok, fmt = check_video_format(temp_path)
            if not is_ok:
                print(f"转码后验证失败：{filepath.name}, format={fmt}")
                if backup_path.exists():
                    shutil.move(backup_path, filepath)
                return False
            
            # 替换原文件
            shutil.move(temp_path, filepath)
            # 删除备份
            if backup_path.exists():
                backup_path.unlink()
            
            print(f"转码成功：{filepath.name}")
            return True
            
        except subprocess.TimeoutExpired:
            print(f"转码超时：{filepath.name}")
            if temp_path.exists():
                temp_path.unlink()
            if backup_path.exists():
                shutil.move(backup_path, filepath)
            return False
        except Exception as e:
            print(f"转码异常：{filepath.name}, error: {e}")
            if temp_path.exists():
                temp_path.unlink()
            if backup_path.exists():
                shutil.move(backup_path, filepath)
            return False
    
    for ext in video_extensions:
        for filepath in scan_dir.rglob(f"*{ext}"):
            scanned_count += 1
            
            # 检查是否已存在（使用文件名 + 文件大小 + 路径三重验证）
            file_size = filepath.stat().st_size
            result = await db.execute(
                select(Video).where(
                    (Video.filename == filepath.name) & 
                    (Video.file_size == file_size)
                )
            )
            existing = result.scalars().first()
            
            # 如果找到同名同大小的文件，进一步检查路径
            if existing:
                # 路径完全相同，确定是同一个文件
                if existing.filepath == str(filepath):
                    print(f"⏭️  跳过已存在：{filepath.name}")
                    continue
                # 路径不同但文件名和大小相同，可能是同一个文件的不同路径
                else:
                    print(f"⏭️  跳过相似文件：{filepath.name} (已存在于：{existing.filepath})")
                    continue
            
            # 确认为新文件
                # 检查视频格式兼容性
                is_compatible, format_name = check_video_format(filepath)
                
                if not is_compatible:
                    print(f"⚠️ 发现不兼容格式：{filepath.name}, format={format_name}")
                    print(f"🔄 开始转码...")
                    
                    if transcode_video(filepath):
                        print(f"✅ 转码成功：{filepath.name}")
                        transcoded_count += 1
                    else:
                        print(f"❌ 转码失败：{filepath.name}，需要人工介入")
                        failed_count += 1
                        # 即使转码失败也记录，但标记状态
                        video = Video(
                            filename=filepath.name,
                            filepath=str(filepath),
                            title=filepath.stem,
                            file_size=filepath.stat().st_size,
                            status="transcode_failed",  # 特殊状态标记
                            has_subtitle=False,
                            has_summary=False,
                        )
                        db.add(video)
                        continue
                
                # 创建新视频记录
                video = Video(
                    filename=filepath.name,
                    filepath=str(filepath),
                    title=filepath.stem,
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
        "transcoded_count": transcoded_count,
        "failed_count": failed_count,
        "failed_files": "请查看日志获取详细信息" if failed_count > 0 else None,
    }




@router.post("/{video_id}/regenerate-kp")
async def regenerate_knowledge_points(
    video_id: int,
    db: AsyncSession = Depends(get_db),
):
    """两阶段重新生成知识点"""
    from sqlalchemy import text, select
    from ..models.video import Video
    from ..services.llm import LLMService
    
    # 获取视频信息
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 加载字幕
    from ..models.subtitle import Subtitle
    result = await db.execute(
        select(Subtitle)
        .where(Subtitle.video_id == video_id)
        .order_by(Subtitle.start)
        .limit(500)
    )
    subtitles = result.scalars().all()
    
    if not subtitles:
        raise HTTPException(status_code=400, detail="视频没有字幕")
    
    # 构建字幕文本
    subtitle_text = "\n".join([f"[{s.start:.1f}] {s.text}" for s in subtitles])
    
    llm = LLMService(backend="alibaba")  # 使用阿里百炼
    
    # 阶段 1：生成知识点
    stage1_prompt = f"""视频：{video.title}

字幕内容:
{subtitle_text[:12000]}

请深入理解内容，总结出 8-12 个关键知识点。
每个知识点包含：title（标题）、description（描述）、type（类型）、keywords（2-3 个关键词）

输出 JSON 格式：
{{
  "knowledge_points": [
    {{"title": "...", "description": "...", "type": "concept", "keywords": ["...", "..."]}}
  ]
}}"""

    print(f"🤖 阶段 1：生成知识点...")
    result1 = await llm.summarize(subtitle_text[:12000], video.title)
    knowledge_points = result1.get('knowledge_points', [])
    
    if not knowledge_points:
        raise HTTPException(status_code=500, detail="知识点生成失败")
    
    print(f"✅ 生成了 {len(knowledge_points)} 个知识点")
    
    # 阶段 2：匹配时间戳
    stage2_prompt = f"""字幕内容:
{subtitle_text[:8000]}

知识点列表:
{json.dumps(knowledge_points, ensure_ascii=False)[:3000]}

请为每个知识点匹配最相关的时间戳（秒）。
基于语义匹配，不是严格字符对应。

输出 JSON 格式：
{{
  "timestamped_knowledge_points": [
    {{"title": "...", "description": "...", "type": "concept", "timestamp": 120.5, "confidence": "high"}}
  ]
}}"""

    print(f"🤖 阶段 2：匹配时间戳...")
    result2 = await llm.summarize(subtitle_text[:8000], "")
    timestamped_kp = result2.get('timestamped_knowledge_points', knowledge_points)
    
    # 保存到数据库
    from ..models.summary import Summary
    result = await db.execute(
        select(Summary).where(Summary.video_id == video_id)
    )
    summary = result.scalar_one_or_none()
    
    if summary:
        summary.knowledge_points = timestamped_kp
        summary.updated_at = datetime.utcnow()
    else:
        summary = Summary(
            video_id=video_id,
            content="",
            knowledge_points=timestamped_kp
        )
        db.add(summary)
    
    await db.commit()
    
    return {
        "message": "知识点重新生成完成",
        "count": len(timestamped_kp),
        "knowledge_points": timestamped_kp[:5]  # 返回前 5 个预览
    }


@router.post("/{video_id}/favorite")
async def toggle_favorite(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user_dependency)
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
    # current_user: User = Depends(get_current_user_dependency)
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
    # current_user: User = Depends(get_current_user_dependency)
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
    # current_user: User = Depends(get_current_user_dependency)
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
    # current_user: User = Depends(get_current_user_dependency)
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




# 新的视频流端点（不需要认证）
async def play_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
):
    """视频播放 - 不需要认证"""
    # 获取视频信息
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 检查文件是否存在
    video_path = Path(video.filepath)
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="视频文件不存在")
    
    # 使用 FileResponse 自动处理 Range 请求
    # 设置正确的响应头
    headers = {
        'Accept-Ranges': 'bytes',
        'Content-Type': 'video/mp4',
        'Content-Disposition': f'inline; filename="{video.filename}"',
        'Cache-Control': 'public, max-age=3600',
    }
    
    return FileResponse(
        str(video_path),
        media_type='video/mp4',
        filename=video.filename,
        headers=headers,
    )


# 测试总结生成 API
@router.post("/{video_id}/test-summarize")
async def test_summarize(
    video_id: int,
    db: AsyncSession = Depends(get_db),
):
    """测试总结生成（不需要认证）"""
    from app.services.llm import LLMService
    from app.models.subtitle import Subtitle
    
    # 获取视频字幕
    result = await db.execute(
        select(Subtitle)
        .where(Subtitle.video_id == video_id)
        .order_by(Subtitle.start)
    )
    subtitles = result.scalars().all()
    
    if not subtitles:
        raise HTTPException(status_code=404, detail="该视频没有字幕")
    
    # 拼接字幕文本（限制长度）
    subtitle_text = "\n".join([sub.text for sub in subtitles[:100]])
    
    # 获取视频标题
    video_result = await db.execute(select(Video).where(Video.id == video_id))
    video = video_result.scalar_one_or_none()
    
    # 调用 LLM 生成总结
    llm_service = LLMService()
    result = await llm_service.summarize(
        subtitle_text=subtitle_text,
        video_title=video.title if video else "未知视频"
    )
    
    return {
        "video_id": video_id,
        "subtitle_count": len(subtitles),
        "summary": result.get("summary", ""),
        "knowledge_points": result.get("knowledge_points", []),
        "token_count": result.get("token_count", 0),
    }
