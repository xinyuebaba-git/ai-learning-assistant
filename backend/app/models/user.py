from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import hashlib

from ..db.base import Base


class User(Base):
    """用户模型"""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # 用户信息
    avatar = Column(String(500), nullable=True)  # 头像 URL
    bio = Column(String(500), nullable=True)  # 个人简介
    
    # 状态
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    
    # 关联
    favorites = relationship("UserFavorite", back_populates="user", cascade="all, delete-orphan")
    notes = relationship("UserNote", back_populates="user", cascade="all, delete-orphan")
    
    @property
    def gravatar(self) -> str:
        """获取 Gravatar 头像"""
        email_hash = hashlib.md5(self.email.lower().encode()).hexdigest()
        return f"https://www.gravatar.com/avatar/{email_hash}?d=identicon"
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
