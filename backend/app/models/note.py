from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from ..db.base import Base


class UserNote(Base):
    """用户笔记模型"""
    
    __tablename__ = "user_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    
    # 笔记内容
    title = Column(String(500), nullable=True)  # 笔记标题
    content = Column(Text, nullable=False)  # 笔记内容
    
    # 关联时间点
    timestamp = Column(Float, nullable=True)  # 关联的视频时间点（秒）
    
    # 标签
    tags = Column(JSON, nullable=True)  # 标签列表 ["重要", "待复习", "公式"]
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    user = relationship("User", back_populates="notes")
    video = relationship("Video", back_populates="notes")
    
    def __repr__(self):
        return f"<UserNote(id={self.id}, user_id={self.user_id}, video_id={self.video_id})>"
