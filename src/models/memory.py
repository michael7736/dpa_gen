"""
记忆系统数据模型
支持项目级和用户级记忆存储
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from enum import Enum
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, Boolean, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from .base import BaseEntity


class MemoryType(str, Enum):
    """记忆类型"""
    PROJECT_CONTEXT = "project_context"  # 项目上下文
    USER_PREFERENCE = "user_preference"  # 用户偏好
    CONVERSATION_HISTORY = "conversation_history"  # 对话历史
    LEARNED_KNOWLEDGE = "learned_knowledge"  # 学习到的知识
    TASK_PROGRESS = "task_progress"  # 任务进度
    SEARCH_PATTERN = "search_pattern"  # 搜索模式


class MemoryScope(str, Enum):
    """记忆作用域"""
    GLOBAL = "global"  # 全局
    PROJECT = "project"  # 项目级
    USER = "user"  # 用户级
    SESSION = "session"  # 会话级


class Memory(BaseEntity):
    """统一的记忆存储表"""
    __tablename__ = "memories"
    
    # 基础字段
    memory_type = Column(String(50), nullable=False, index=True, comment="记忆类型")
    scope = Column(String(20), nullable=False, index=True, comment="作用域")
    
    # 关联字段
    user_id = Column(String, ForeignKey("users.id"), index=True, comment="用户ID")
    project_id = Column(String, ForeignKey("projects.id"), index=True, comment="项目ID")
    session_id = Column(String, index=True, comment="会话ID")
    
    # 记忆内容
    key = Column(String(255), nullable=False, comment="记忆键")
    content = Column(JSONB, nullable=False, comment="记忆内容")
    summary = Column(Text, comment="记忆摘要")
    
    # 元数据
    importance = Column(Float, default=0.5, comment="重要性评分 0-1")
    access_count = Column(Integer, default=0, comment="访问次数")
    last_accessed_at = Column(DateTime(timezone=True), comment="最后访问时间")
    expires_at = Column(DateTime(timezone=True), comment="过期时间")
    
    # 关系
    user = relationship("User", back_populates="memories")
    project = relationship("Project", back_populates="memories")
    
    # 复合索引
    __table_args__ = (
        Index('idx_memory_lookup', 'memory_type', 'scope', 'user_id', 'project_id', 'key'),
        Index('idx_memory_importance', 'importance', 'last_accessed_at'),
    )


class ProjectMemory(BaseEntity):
    """项目记忆专用表（性能优化）"""
    __tablename__ = "project_memories"
    
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    project = relationship("Project")
    
    # 项目上下文
    context_summary = Column(Text, comment="项目上下文摘要")
    key_concepts = Column(JSONB, default=list, comment="关键概念列表")
    research_goals = Column(JSONB, default=list, comment="研究目标")
    
    # 知识积累
    learned_facts = Column(JSONB, default=list, comment="学习到的事实")
    important_documents = Column(JSONB, default=list, comment="重要文档列表")
    frequent_queries = Column(JSONB, default=list, comment="常见查询")
    
    # 工作进度
    completed_tasks = Column(JSONB, default=list, comment="已完成任务")
    pending_tasks = Column(JSONB, default=list, comment="待处理任务")
    milestones = Column(JSONB, default=list, comment="里程碑")
    
    # 统计信息
    total_documents = Column(Integer, default=0, comment="文档总数")
    total_queries = Column(Integer, default=0, comment="查询总数")
    avg_confidence = Column(Float, default=0.0, comment="平均置信度")
    
    # 更新追踪
    last_activity_at = Column(DateTime(timezone=True), default=datetime.now, comment="最后活动时间")
    memory_version = Column(Integer, default=1, comment="记忆版本")


class UserMemory(BaseEntity):
    """用户记忆专用表"""
    __tablename__ = "user_memories"
    
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    user = relationship("User")
    
    # 用户偏好
    language_preference = Column(String(10), default="zh", comment="语言偏好")
    response_style = Column(String(50), default="concise", comment="回答风格")
    expertise_level = Column(String(20), default="intermediate", comment="专业水平")
    
    # 交互模式
    preferred_chunk_size = Column(Integer, default=5, comment="偏好的结果数量")
    detail_level = Column(String(20), default="balanced", comment="详细程度")
    include_sources = Column(Boolean, default=True, comment="是否包含来源")
    
    # 知识领域
    interests = Column(JSONB, default=list, comment="兴趣领域")
    expertise_areas = Column(JSONB, default=list, comment="专长领域")
    avoided_topics = Column(JSONB, default=list, comment="避免的主题")
    
    # 使用习惯
    active_hours = Column(JSONB, default=dict, comment="活跃时段")
    query_patterns = Column(JSONB, default=list, comment="查询模式")
    favorite_projects = Column(JSONB, default=list, comment="常用项目")
    
    # 个性化设置
    custom_prompts = Column(JSONB, default=dict, comment="自定义提示词")
    shortcuts = Column(JSONB, default=dict, comment="快捷方式")
    ui_preferences = Column(JSONB, default=dict, comment="界面偏好")


class ConversationMemory(BaseEntity):
    """对话记忆表"""
    __tablename__ = "conversation_memories"
    
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False, index=True)
    conversation = relationship("Conversation", back_populates="memories")
    
    # 对话上下文
    turn_number = Column(Integer, comment="对话轮次")
    user_message = Column(Text, comment="用户消息")
    assistant_response = Column(Text, comment="助手回复")
    
    # 关键信息提取
    entities_mentioned = Column(JSONB, default=list, comment="提到的实体")
    topics_discussed = Column(JSONB, default=list, comment="讨论的主题")
    decisions_made = Column(JSONB, default=list, comment="做出的决定")
    
    # 记忆重要性
    is_important = Column(Boolean, default=False, comment="是否重要")
    importance_reason = Column(Text, comment="重要原因")
    
    # 关联信息
    referenced_documents = Column(JSONB, default=list, comment="引用的文档")
    generated_tasks = Column(JSONB, default=list, comment="生成的任务")


# Pydantic模型
from pydantic import BaseModel, Field, validator


class MemoryCreate(BaseModel):
    """创建记忆的模型"""
    memory_type: MemoryType
    scope: MemoryScope
    key: str
    content: Dict[str, Any]
    summary: Optional[str] = None
    importance: float = Field(0.5, ge=0, le=1)
    expires_in_hours: Optional[int] = None
    
    # 关联ID
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    session_id: Optional[str] = None
    
    @validator('scope')
    def validate_scope_ids(cls, v, values):
        """验证作用域和ID的匹配"""
        if v == MemoryScope.PROJECT and not values.get('project_id'):
            raise ValueError("Project scope requires project_id")
        if v == MemoryScope.USER and not values.get('user_id'):
            raise ValueError("User scope requires user_id")
        return v


class MemoryUpdate(BaseModel):
    """更新记忆的模型"""
    content: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    importance: Optional[float] = Field(None, ge=0, le=1)
    extend_expiry_hours: Optional[int] = None


class MemoryQuery(BaseModel):
    """查询记忆的模型"""
    memory_types: Optional[List[MemoryType]] = None
    scope: Optional[MemoryScope] = None
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    key_pattern: Optional[str] = None
    min_importance: Optional[float] = Field(None, ge=0, le=1)
    include_expired: bool = False
    limit: int = Field(100, ge=1, le=1000)


class ProjectMemoryUpdate(BaseModel):
    """更新项目记忆"""
    context_summary: Optional[str] = None
    key_concepts: Optional[List[str]] = None
    research_goals: Optional[List[Dict[str, Any]]] = None
    learned_facts: Optional[List[Dict[str, Any]]] = None
    important_documents: Optional[List[str]] = None
    completed_tasks: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "context_summary": "研究大语言模型在教育领域的应用",
                "key_concepts": ["LLM", "教育技术", "个性化学习"],
                "learned_facts": [
                    {"fact": "GPT-4在数学教学中表现优秀", "confidence": 0.9}
                ]
            }
        }


class UserPreferenceUpdate(BaseModel):
    """更新用户偏好"""
    language_preference: Optional[str] = None
    response_style: Optional[Literal["concise", "detailed", "balanced"]] = None
    expertise_level: Optional[Literal["beginner", "intermediate", "expert"]] = None
    preferred_chunk_size: Optional[int] = Field(None, ge=1, le=20)
    interests: Optional[List[str]] = None
    custom_prompts: Optional[Dict[str, str]] = None