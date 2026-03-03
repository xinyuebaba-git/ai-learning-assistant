from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import os

from ..db.base import get_db
from ..models.user import User
from ..api.auth import get_current_user_dependency


router = APIRouter()


# ============ Pydantic 模型 ============

class SearchResult(BaseModel):
    """搜索结果项"""
    video_id: int
    video_title: str
    video_filename: str
    text: str  # 匹配的字幕或总结文本
    text_type: str  # subtitle / summary / knowledge_point
    timestamp: Optional[float] = None  # 时间点（秒）
    score: float  # 相关性分数


class SearchResponse(BaseModel):
    """搜索响应"""
    query: str
    total: int
    results: List[SearchResult]


# ============ API 路由 ============

# @router.get("", response_model=SearchResponse)  # 临时禁用
async def search_disabled():
    # 临时返回空结果，避免 ChromaDB 兼容性问题
    return {"results": [], "total": 0}
async def search_disabled():
    return {"results": [], "message": "搜索功能维护中"}
async def search_videos(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(20, ge=1, le=100),
    search_type: str = Query("all", description="搜索类型：all/subtitle/summary"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """语义搜索视频内容"""
    from ..services.search import SearchService
    
    search_service = SearchService()
    
    try:
        results = await search_service.search(
            query=q,
            limit=limit,
            search_type=search_type,
        )
        
        return SearchResponse(
            query=q,
            total=len(results),
            results=[
                SearchResult(
                    video_id=r["video_id"],
                    video_title=r["video_title"],
                    video_filename=r["video_filename"],
                    text=r["text"],
                    text_type=r["text_type"],
                    timestamp=r.get("timestamp"),
                    score=r["score"],
                )
                for r in results
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败：{str(e)}")


@router.get("/suggestions")
async def search_suggestions(
    q: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """获取搜索建议"""
    from ..services.search import SearchService
    
    search_service = SearchService()
    
    try:
        suggestions = await search_service.get_suggestions(query=q, limit=limit)
        return {"query": q, "suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取建议失败：{str(e)}")
