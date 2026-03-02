from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from ..db.base import Base


class Subtitle(Base):
    """字幕条目模型"""
    
    __tablename__ = "subtitles"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    
    # 字幕内容
    index = Column(Integer, nullable=False)  # 字幕序号
    start = Column(Float, nullable=False)  # 开始时间（秒）
    end = Column(Float, nullable=False)  # 结束时间（秒）
    text = Column(Text, nullable=False)  # 字幕文本
    language = Column(String(20), default="zh-CN")  # 语言
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联
    video = relationship("Video", back_populates="subtitles")
    
    # 索引
    __table_args__ = (
        Index("idx_subtitle_video_time", "video_id", "start"),
        Index("idx_subtitle_text", "text", postgresql_using="gin"),
    )
    
    def __repr__(self):
        return f"<Subtitle(id={self.id}, video_id={self.video_id}, start={self.start})>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "index": self.index,
            "start": self.start,
            "end": self.end,
            "text": self.text,
            "language": self.language,
        }
