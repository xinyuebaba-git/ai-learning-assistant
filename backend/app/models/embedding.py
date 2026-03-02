from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from ..db.base import Base


class Embedding(Base):
    """向量嵌入模型（用于语义搜索）"""
    
    __tablename__ = "embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    
    # 嵌入信息
    text = Column(Text, nullable=False)  # 原始文本（字幕片段或总结）
    text_type = Column(String(50), nullable=False)  # subtitle / summary / knowledge_point
    
    # 关联时间点（对于字幕片段）
    start = Column(Float, nullable=True)  # 开始时间
    end = Column(Float, nullable=True)  # 结束时间
    
    # 向量数据（ChromaDB 存储，这里只存元数据）
    embedding_id = Column(String(100), nullable=True)  # ChromaDB 中的 ID
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联
    video = relationship("Video", back_populates="embeddings")
    
    # 索引
    __table_args__ = (
        Index("idx_embedding_video_type", "video_id", "text_type"),
        Index("idx_embedding_text", "text", postgresql_using="gin"),
    )
    
    def __repr__(self):
        return f"<Embedding(id={self.id}, video_id={self.video_id}, type={self.text_type})>"
