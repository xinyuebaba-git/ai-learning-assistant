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
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    video_path = Path(video.filepath)
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="视频文件不存在")
    
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
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    video_path = Path(video.filepath)
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="视频文件不存在")
    
    file_size = video_path.stat().st_size
    
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
):
    """扫描视频文件，并检查格式兼容性"""
    from ..core.config import settings
    import subprocess
    import json
    
    scan_dir = Path(request.directory) if request and request.directory else Path(settings.VIDEO_DIR)
    
    if not scan_dir.exists():
        raise HTTPException(status_code=400, detail=f"目录不存在：{scan_dir}")
    
    video_extensions = {".mp4", ".mov", ".mkv", ".avi", ".m4v", ".webm", ".flv", ".wmv"}
    COMPATIBLE_FORMATS = {"mov", "mp4", "m4a", "3gp", "3g2", "mj2"}
    
    scanned_count = 0
    new_count = 0
    transcoded_count = 0
    failed_count = 0
    
    def check_video_format(filepath: Path) -> tuple[bool, str | None]:
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=format_name", "-of", "json", str(filepath)],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                return False, None
            
            data = json.loads(result.stdout)
            format_name = data.get("format", {}).get("format_name", "")
            is_compatible = any(f in format_name for f in COMPATIBLE_FORMATS)
            return is_compatible, format_name
        except Exception as e:
            print(f"检查视频格式失败 {filepath}: {e}")
            return False, None
    
    def transcode_video(filepath: Path) -> bool:
        backup_path = filepath.with_suffix(filepath.suffix + ".backup")
        temp_path = filepath.with_suffix(filepath.suffix + ".transcoding.mp4")
        
        try:
            import shutil
            shutil.copy2(filepath, backup_path)
            print(f"已备份原文件：{backup_path}")
            
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
                if backup_path.exists():
                    shutil.move(backup_path, filepath)
                return False
            
            is_ok, fmt = check_video_format(temp_path)
            if not is_ok:
                print(f"转码后验证失败：{filepath.name}, format={fmt}")
                if backup_path.exists():
                    shutil.move(backup_path, filepath)
                return False
            
            shutil.move(temp_path, filepath)
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
            
            file_size = filepath.stat().st_size
            result = await db.execute(
                select(Video).where(
                    (Video.filename == filepath.name) & 
                    (Video.file_size == file_size)
                )
            )
            existing = result.scalars().first()
            
            if existing:
                if existing.filepath == str(filepath):
                    print(f"⏭️  跳过已存在：{filepath.name}")
                    continue
                else:
                    print(f"⏭️  跳过相似文件：{filepath.name} (已存在于：{existing.filepath})")
                    continue
            
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
                    video = Video(
                        filename=filepath.name,
                        filepath=str(filepath),
                        title=filepath.stem,
                        file_size=filepath.stat().st_size,
                        status="transcode_failed",
                        has_subtitle=False,
                        has_summary=False,
                    )
                    db.add(video)
                    continue
            
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
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """异步重新生成知识点 - 立即返回任务状态"""
    from sqlalchemy import select
    from ..models.video import Video
    
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    from ..models.subtitle import Subtitle
    result = await db.execute(
        select(Subtitle)
        .where(Subtitle.video_id == video_id)
        .order_by(Subtitle.start)
    )
    subtitles = result.scalars().all()
    
    if not subtitles:
        raise HTTPException(status_code=400, detail="视频没有字幕")
    
    # 启动后台任务
    background_tasks.add_task(_do_regenerate_kp, video_id, video.title, subtitles)
    
    return {
        "message": "知识点重新生成任务已启动，请稍候刷新页面查看结果",
        "video_id": video_id,
        "status": "processing",
    }


async def _do_regenerate_kp(
    video_id: int,
    video_title: str,
    subtitles: list,
):
    """后台执行知识点重新生成"""
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
    from ..db.base import AsyncSessionLocal
    from ..services.llm import LLMService
    import asyncio
    import re
    import json
    
    db: AsyncSession = AsyncSessionLocal()
    
    try:
        video_duration = max(s.end for s in subtitles) if subtitles else None
        duration_minutes = int(video_duration // 60) if video_duration else 0
        duration_info = f"{int(video_duration)}秒（{duration_minutes}分钟）" if video_duration else "未知"
        
        print(f"📊 视频时长：{duration_info}")
        
        subtitle_text = "\n".join([f"[{s.start:.1f}s] {s.text}" for s in subtitles])
        
        llm = LLMService(backend="alibaba")
        client = llm._get_client()
        
        print(f"🤖 阶段 1：生成知识点...")
        
        kp_prompt = f"""视频标题：{video_title}
视频时长：{duration_info}

字幕内容（带时间戳）:
{subtitle_text[:50000]}

请分析视频内容，提取 15-20 个关键知识点，均匀分布在整个视频中。

输出 JSON 格式（只输出 JSON，不要其他内容）:
{{
  "knowledge_points": [
    {{"title": "知识点标题", "description": "知识点描述", "type": "concept"}}
  ]
}}

知识点类型包括：concept（概念）, formula（公式）, example（示例）, key_point（重点）"""

        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=llm.model,
            messages=[
                {"role": "system", "content": "你是一个专业的教育内容分析师，输出纯 JSON 格式"},
                {"role": "user", "content": kp_prompt},
            ],
            response_format={"type": "json_object"},
        )
        
        result_text = response.choices[0].message.content
        
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            knowledge_points = result.get('knowledge_points', [])
        else:
            knowledge_points = []
        
        if not knowledge_points:
            print(f"❌ 知识点生成失败")
            return
        
        print(f"✅ 生成了 {len(knowledge_points)} 个知识点")
        
        print(f"🤖 阶段 2：为每个知识点匹配时间戳...")
        
        timestamped_kp = []
        for kp in knowledge_points:
            title = kp.get('title', '')
            description = kp.get('description', '')
            
            matched_subtitle = None
            max_overlap = 0
            
            for sub in subtitles:
                text_lower = sub.text.lower()
                title_lower = title.lower()
                desc_lower = description.lower()
                
                overlap = 0
                for word in title_lower.split():
                    if word in text_lower:
                        overlap += 1
                for word in desc_lower.split()[:10]:
                    if word in text_lower:
                        overlap += 1
                
                if overlap > max_overlap:
                    max_overlap = overlap
                    matched_subtitle = sub
            
            if matched_subtitle and max_overlap > 0:
                timestamp = matched_subtitle.start
                confidence = "high"
            else:
                if video_duration:
                    idx = knowledge_points.index(kp)
                    total = len(knowledge_points)
                    timestamp = (idx / (total - 1)) * video_duration if total > 1 else 0
                else:
                    timestamp = 0
                confidence = "estimated"
            
            timestamped_kp.append({
                **kp,
                "timestamp": timestamp,
                "confidence": confidence,
                "matched_text": matched_subtitle.text if matched_subtitle else "",
            })
            
            print(f"  - [{timestamp:.1f}s] {kp.get('title', '未知')}")
        
        print(f"✅ 匹配完成，{len([kp for kp in timestamped_kp if kp['confidence'] == 'high'])} 个高置信度匹配")
        
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
        print(f"✅ 知识点重新生成完成，已保存")
        
    except Exception as e:
        print(f"❌ 知识点重新生成失败：{e}")
        import traceback
        traceback.print_exc()
    finally:
        await db.close()


@router.post("/{video_id}/favorite")
async def toggle_favorite(
    video_id: int,
    db: AsyncSession = Depends(get_db),
):
    """切换收藏状态"""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 注意：当前未启用认证，跳过用户检查
    # 如需认证，取消注释下面的代码
    # result = await db.execute(
    #     select(UserFavorite).where(
    #         UserFavorite.user_id == current_user.id,
    #         UserFavorite.video_id == video_id
    #     )
    # )
    # favorite = result.scalar_one_or_none()
    
    return {"message": "收藏功能待实现"}


@router.get("/{video_id}/subtitle")
async def get_subtitle(
    video_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取视频字幕"""
    from ..models.subtitle import Subtitle
    
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    if not video.has_subtitle:
        raise HTTPException(status_code=404, detail="该视频暂无字幕")
    
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
):
    """获取视频总结"""
    from ..models.summary import Summary
    
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    if not video.has_summary:
        raise HTTPException(status_code=404, detail="该视频暂无总结")
    
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
):
    """处理视频（异步任务队列）"""
    from app.tasks.video_tasks import process_video_task
    
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    if video.status == VideoStatus.SUMMARIZED:
        return {
            "message": "视频已处理完成",
            "status": video.status,
        }
    
    video.status = VideoStatus.SUBTITLING
    video.updated_at = datetime.utcnow()
    await db.commit()
    
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
):
    """获取视频处理进度"""
    from app.tasks.video_tasks import get_task_progress
    from celery.result import AsyncResult
    
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    status_info = {
        "video_id": video_id,
        "video_status": video.status,
        "has_subtitle": video.has_subtitle,
        "has_summary": video.has_summary,
        "error_message": video.error_message,
        "processed_at": video.processed_at,
    }
    
    if task_id:
        task_result = AsyncResult(task_id, app=celery_app)
        status_info["task"] = {
            "task_id": task_id,
            "status": task_result.status,
            "ready": task_result.ready(),
        }
    
    return status_info


# 测试总结生成 API
@router.post("/{video_id}/test-summarize")
async def test_summarize(
    video_id: int,
    db: AsyncSession = Depends(get_db),
):
    """测试总结生成（不需要认证）"""
    from app.services.llm import LLMService
    from app.models.subtitle import Subtitle
    
    result = await db.execute(
        select(Subtitle)
        .where(Subtitle.video_id == video_id)
        .order_by(Subtitle.start)
    )
    subtitles = result.scalars().all()
    
    if not subtitles:
        raise HTTPException(status_code=404, detail="该视频没有字幕")
    
    subtitle_text = "\n".join([sub.text for sub in subtitles[:100]])
    
    video_result = await db.execute(select(Video).where(Video.id == video_id))
    video = video_result.scalar_one_or_none()
    
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
