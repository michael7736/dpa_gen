"""
记忆模型定义
"""
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Integer, Text, JSON, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.database.postgres import Base


class MemoryType(str, Enum):
    """记忆类型"""
    SEMANTIC = "semantic"     # 语义记忆
    EPISODIC = "episodic"     # 情景记忆
    WORKING = "working"       # 工作记忆
    DECLARATIVE = "declarative"  # 陈述性记忆
    PROCEDURAL = "procedural"    # 程序性记忆


class MemoryStatus(str, Enum):
    """记忆状态"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Memory(Base):
    """记忆模型"""
    __tablename__ = "memories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100), nullable=False, index=True)
    project_id = Column(String(100), nullable=True, index=True)
    memory_type = Column(SQLEnum(MemoryType), nullable=False)
    scope = Column(String(50), nullable=True, default="project")
    key = Column(String(200), nullable=True, index=True)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    importance = Column(Integer, default=5)  # 0-10 scale
    embedding = Column(JSON, nullable=True)  # 存储向量嵌入
    meta_data = Column(JSON, nullable=True, default={})
    status = Column(SQLEnum(MemoryStatus), default=MemoryStatus.ACTIVE)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "project_id": self.project_id,
            "memory_type": self.memory_type.value,
            "content": self.content,
            "metadata": self.meta_data,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ProjectMemory(Base):
    """项目记忆模型"""
    __tablename__ = "project_memories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(String(100), nullable=False, unique=True, index=True)
    context = Column(Text, nullable=True)
    goals = Column(JSON, nullable=True, default=[])
    key_findings = Column(JSON, nullable=True, default=[])
    meta_data = Column(JSON, nullable=True, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserMemory(Base):
    """用户记忆模型"""
    __tablename__ = "user_memories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100), nullable=False, index=True)
    preferences = Column(JSON, nullable=True, default={})
    interaction_history = Column(JSON, nullable=True, default=[])
    meta_data = Column(JSON, nullable=True, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConversationMemory(Base):
    """会话记忆模型"""
    __tablename__ = "conversation_memories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    project_id = Column(String(100), nullable=True, index=True)
    messages = Column(JSON, nullable=False, default=[])
    summary = Column(Text, nullable=True)
    meta_data = Column(JSON, nullable=True, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)