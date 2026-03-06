from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Optional

from ..db.base import get_db


router = APIRouter()


# ============ Pydantic 模型 ============

class SearchResult(BaseModel):
    """搜索结果项"""
    video_id: int
    video_title: str
    video_filename: str
    text: str
    text_type: str
    timestamp: Optional[float] = None
    score: float


class SearchResponse(BaseModel):
    """搜索响应"""
    query: str
    total: int
    results: List[SearchResult]


# ============ API 路由 ============

@router.get("", response_model=SearchResponse)
async def search_videos(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(50, ge=1, le=200),
    search_type: str = Query("all", description="搜索类型：all/subtitle/summary"),
    db: AsyncSession = Depends(get_db),
):
    """基于数据库的全文搜索"""
    results = []
    
    # 搜索字幕
    if search_type in ["all", "subtitle"]:
        query = text("""
            SELECT v.id as video_id, v.title as video_title, v.filename as video_filename,
                   s.text, 'subtitle' as text_type, s.start as timestamp, 1.0 as score
            FROM subtitles s
            JOIN videos v ON s.video_id = v.id
            WHERE s.text LIKE :keyword
            LIMIT :limit
        """)
        result = await db.execute(query, {"keyword": f"%{q}%", "limit": limit})
        for row in result:
            results.append({
                "video_id": row.video_id,
                "video_title": row.video_title or row.video_filename,
                "video_filename": row.video_filename,
                "text": row.text,
                "text_type": "subtitle",
                "timestamp": float(row.timestamp) if row.timestamp else None,
                "score": row.score,
            })
    
    # 搜索总结
    if search_type in ["all", "summary"] and len(results) < limit:
        query = text("""
            SELECT v.id as video_id, v.title as video_title, v.filename as video_filename,
                   sm.content as text, 'summary' as text_type, NULL as timestamp, 0.9 as score
            FROM summaries sm
            JOIN videos v ON sm.video_id = v.id
            WHERE sm.content LIKE :keyword
            LIMIT :limit
        """)
        remaining = limit - len(results)
        result = await db.execute(query, {"keyword": f"%{q}%", "limit": remaining})
        for row in result:
            text_preview = row.text[:200] + "..." if len(row.text) > 200 else row.text
            results.append({
                "video_id": row.video_id,
                "video_title": row.video_title or row.video_filename,
                "video_filename": row.video_filename,
                "text": text_preview,
                "text_type": "summary",
                "timestamp": None,
                "score": row.score,
            })
    
    return SearchResponse(
        query=q,
        total=len(results),
        results=results
    )


@router.get("/suggestions")
async def search_suggestions(
    q: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
):
    """获取搜索建议（基于视频标题）"""
    query = text("""
        SELECT DISTINCT title, filename
        FROM videos
        WHERE title LIKE :keyword OR filename LIKE :keyword
        LIMIT :limit
    """)
    result = await db.execute(query, {"keyword": f"%{q}%", "limit": limit})
    
    suggestions = []
    for row in result:
        suggestions.append(row.title or row.filename)
    
    return {"query": q, "suggestions": suggestions}
