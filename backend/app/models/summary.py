from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from ..db.base import Base


class Summary(Base):
    """视频内容总结模型"""
    
    __tablename__ = "summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # 总结内容
    content = Column(Text, nullable=False)  # 完整总结文本
    
    # 知识点列表（JSON 格式存储）
    # 格式：[{"id": 1, "timestamp": 120.5, "title": "xxx", "description": "xxx", "type": "concept"}]
    knowledge_points = Column(JSON, nullable=True)
    
    # 元数据
    model_backend = Column(String(50), nullable=True)  # 使用的 LLM 后端
    model_name = Column(String(100), nullable=True)  # 使用的模型名称
    token_count = Column(Integer, nullable=True)  # 消耗的 token 数
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    video = relationship("Video", back_populates="summary")
    
    def __repr__(self):
        return f"<Summary(id={self.id}, video_id={self.video_id})>"


class KnowledgePoint(Base):
    """知识点独立模型（可选，用于更复杂的查询）"""
    
    __tablename__ = "knowledge_points"
    
    id = Column(Integer, primary_key=True, index=True)
    summary_id = Column(Integer, ForeignKey("summaries.id", ondelete="CASCADE"), nullable=False)
    
    # 知识点信息
    title = Column(String(500), nullable=False)  # 知识点标题
    description = Column(Text, nullable=True)  # 详细描述
    timestamp = Column(Float, nullable=False)  # 时间点（秒）
    point_type = Column(String(50), nullable=True)  # 类型：concept/formula/example/key_point
    
    # 标签
    tags = Column(JSON, nullable=True)  # 标签列表
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联
    summary = relationship("Summary", backref="knowledge_points_list")
    
    def __repr__(self):
        return f"<KnowledgePoint(id={self.id}, title={self.title}, timestamp={self.timestamp})>"
