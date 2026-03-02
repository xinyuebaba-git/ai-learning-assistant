from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from ..db.base import Base


class VideoStatus(str, enum.Enum):
    """视频处理状态"""
    PENDING = "pending"  # 待处理
    SCANNED = "scanned"  # 已扫描
    SUBTITLING = "subtitling"  # 字幕生成中
    SUBTITLED = "subtitled"  # 字幕已完成
    SUMMARIZING = "summarizing"  # 总结生成中
    SUMMARIZED = "summarized"  # 总结已完成
    FAILED = "failed"  # 处理失败
    ERROR = "error"  # 错误状态


class Video(Base):
    """视频模型"""
    
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 文件信息
    filename = Column(String(500), nullable=False)  # 文件名
    filepath = Column(String(1000), nullable=False)  # 完整路径
    original_path = Column(String(1000), nullable=True)  # 原始路径（如果不是在视频目录）
    
    # 元数据
    title = Column(String(500), nullable=True)  # 标题（可从文件名提取）
    description = Column(Text, nullable=True)  # 描述
    duration = Column(Float, nullable=True)  # 时长（秒）
    file_size = Column(Integer, nullable=True)  # 文件大小（字节）
    
    # 处理状态
    status = Column(SQLEnum(VideoStatus), default=VideoStatus.PENDING)
    error_message = Column(Text, nullable=True)  # 错误信息
    
    # 字幕信息
    has_subtitle = Column(Boolean, default=False)
    subtitle_path = Column(String(1000), nullable=True)
    subtitle_language = Column(String(20), nullable=True)
    subtitle_source = Column(String(50), nullable=True)  # asr / manual / external
    
    # 总结信息
    has_summary = Column(Boolean, default=False)
    summary_path = Column(String(1000), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)  # 处理完成时间
    
    # 关联
    subtitles = relationship("Subtitle", back_populates="video", cascade="all, delete-orphan")
    summary = relationship("Summary", back_populates="video", uselist=False, cascade="all, delete-orphan")
    favorites = relationship("UserFavorite", back_populates="video", cascade="all, delete-orphan")
    notes = relationship("UserNote", back_populates="video", cascade="all, delete-orphan")
    embeddings = relationship("Embedding", back_populates="video", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Video(id={self.id}, filename={self.filename}, status={self.status})>"
