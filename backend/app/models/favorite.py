from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from ..db.base import Base


class UserFavorite(Base):
    """用户收藏模型"""
    
    __tablename__ = "user_favorites"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联
    user = relationship("User", back_populates="favorites")
    video = relationship("Video", back_populates="favorites")
    
    # 唯一约束（同一用户不能重复收藏同一视频）
    __table_args__ = (
        UniqueConstraint("user_id", "video_id", name="uq_user_video_favorite"),
    )
    
    def __repr__(self):
        return f"<UserFavorite(user_id={self.user_id}, video_id={self.video_id})>"
