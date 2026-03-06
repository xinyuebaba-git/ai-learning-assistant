from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime

from ..db.base import get_db
from ..models.note import UserNote
from ..models.user import User
from ..api.auth import get_current_user_dependency


router = APIRouter()


# ============ Pydantic 模型 ============

class NoteCreate(BaseModel):
    """创建笔记请求"""
    video_id: int
    title: Optional[str] = None
    content: str
    timestamp: Optional[float] = None  # 关联的视频时间点
    tags: Optional[List[str]] = None


class NoteUpdate(BaseModel):
    """更新笔记请求"""
    title: Optional[str] = None
    content: Optional[str] = None
    timestamp: Optional[float] = None
    tags: Optional[List[str]] = None


from pydantic import field_validator

class NoteResponse(BaseModel):
    """笔记响应"""
    id: int
    video_id: int
    title: str | None = None
    content: str
    timestamp: float | None = None
    tags: List[str] | None = None
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True
    
    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def convert_datetime_to_str(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v


# ============ API 路由 ============

@router.get("", response_model=List[NoteResponse])
async def list_notes(
    video_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """获取笔记列表"""
    query = select(UserNote).where(UserNote.user_id == current_user.id)
    
    # 按视频过滤
    if video_id:
        query = query.where(UserNote.video_id == video_id)
    
    # 排序
    query = query.order_by(UserNote.created_at.desc())
    
    # 分页
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    notes = result.scalars().all()
    
    return notes


@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    note_data: NoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """创建笔记"""
    from ..models.video import Video
    
    # 检查视频是否存在
    result = await db.execute(select(Video).where(Video.id == note_data.video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    
    # 创建笔记
    note = UserNote(
        user_id=current_user.id,
        video_id=note_data.video_id,
        title=note_data.title,
        content=note_data.content,
        timestamp=note_data.timestamp,
        tags=note_data.tags,
    )
    
    db.add(note)
    await db.commit()
    await db.refresh(note)
    
    return note


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """获取笔记详情"""
    result = await db.execute(
        select(UserNote).where(
            UserNote.id == note_id,
            UserNote.user_id == current_user.id
        )
    )
    note = result.scalar_one_or_none()
    
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    
    return note


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: int,
    note_data: NoteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """更新笔记"""
    result = await db.execute(
        select(UserNote).where(
            UserNote.id == note_id,
            UserNote.user_id == current_user.id
        )
    )
    note = result.scalar_one_or_none()
    
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    
    # 更新字段
    update_data = note_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(note, field, value)
    
    note.updated_at = datetime.utcnow()
    
    db.add(note)
    await db.commit()
    await db.refresh(note)
    
    return note


@router.delete("/{note_id}")
async def delete_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """删除笔记"""
    result = await db.execute(
        select(UserNote).where(
            UserNote.id == note_id,
            UserNote.user_id == current_user.id
        )
    )
    note = result.scalar_one_or_none()
    
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    
    await db.delete(note)
    await db.commit()
    
    return {"message": "笔记已删除"}
