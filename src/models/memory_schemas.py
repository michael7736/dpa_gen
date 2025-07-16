"""
记忆系统的Pydantic模型定义
"""
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    """记忆类型"""
    SEMANTIC = "semantic"     # 语义记忆
    EPISODIC = "episodic"     # 情景记忆
    WORKING = "working"       # 工作记忆
    DECLARATIVE = "declarative"  # 陈述性记忆
    PROCEDURAL = "procedural"    # 程序性记忆


class MemoryScope(str, Enum):
    """记忆作用域"""
    USER = "user"           # 用户级别
    PROJECT = "project"     # 项目级别
    CONVERSATION = "conversation"  # 会话级别
    GLOBAL = "global"       # 全局级别


class MemoryStatus(str, Enum):
    """记忆状态"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class MemoryBase(BaseModel):
    """记忆基础模型"""
    content: str
    memory_type: MemoryType
    project_id: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class MemoryCreate(MemoryBase):
    """创建记忆"""
    user_id: str
    scope: Optional[MemoryScope] = MemoryScope.PROJECT
    key: Optional[str] = None
    summary: Optional[str] = None
    importance: Optional[float] = Field(default=0.5, ge=0.0, le=1.0)
    expires_in_hours: Optional[int] = None


class MemoryUpdate(BaseModel):
    """更新记忆"""
    content: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None
    status: Optional[MemoryStatus] = None


class MemoryResponse(MemoryBase):
    """记忆响应"""
    id: str
    user_id: str
    status: MemoryStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MemoryQuery(BaseModel):
    """记忆查询"""
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    memory_type: Optional[MemoryType] = None
    status: Optional[MemoryStatus] = MemoryStatus.ACTIVE
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class ProjectMemoryUpdate(BaseModel):
    """项目记忆更新"""
    project_id: str
    context: Optional[str] = None
    goals: Optional[List[str]] = None
    key_findings: Optional[List[str]] = None
    meta_data: Optional[Dict[str, Any]] = None


class UserPreferenceUpdate(BaseModel):
    """用户偏好更新"""
    user_id: str
    preferences: Dict[str, Any]
    category: Optional[str] = "general"