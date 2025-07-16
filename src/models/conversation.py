"""
对话数据模型
"""

from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import enum
from .base import BaseEntity


class MessageRole(enum.Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(enum.Enum):
    """消息类型枚举"""
    TEXT = "text"
    QUERY = "query"
    ANALYSIS = "analysis"
    SUMMARY = "summary"
    COMPARISON = "comparison"
    RISK_ASSESSMENT = "risk_assessment"


class Conversation(BaseEntity):
    """对话模型"""
    __tablename__ = "conversations"
    
    title = Column(String(200), nullable=False, index=True)
    
    # 关联用户和项目
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True, index=True)
    
    # 对话配置
    settings = Column(Text, nullable=True)  # JSON格式的对话设置
    
    # 统计信息
    message_count = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    
    # 关系
    user = relationship("User", back_populates="conversations")
    project = relationship("Project", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    # memories = relationship("ConversationMemory", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, title='{self.title}', user_id={self.user_id}, messages={self.message_count})>"


class Message(BaseEntity):
    """消息模型"""
    __tablename__ = "messages"
    
    # 关联对话
    conversation_id = Column(PG_UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    
    # 消息信息
    role = Column(Enum(MessageRole), nullable=False, index=True)
    message_type = Column(Enum(MessageType), default=MessageType.TEXT, nullable=False, index=True)
    content = Column(Text, nullable=False)
    
    # 消息序号
    sequence_number = Column(Integer, nullable=False, index=True)
    
    # 处理信息
    processing_time = Column(Float, nullable=True)  # 处理时间（秒）
    token_count = Column(Integer, nullable=True)  # token数量
    
    # 引用信息
    sources = Column(Text, nullable=True)  # JSON格式的来源信息
    citations = Column(Text, nullable=True)  # JSON格式的引用信息
    
    # 质量评分
    quality_score = Column(Float, nullable=True)  # 回答质量评分
    relevance_score = Column(Float, nullable=True)  # 相关性评分
    
    # 元数据
    message_metadata = Column(Text, nullable=True)  # JSON格式的元数据
    
    # 关系
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, role='{self.role.value}', seq={self.sequence_number})>" 