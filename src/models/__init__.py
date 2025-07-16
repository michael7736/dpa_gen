"""
数据模型模块
定义所有的SQLAlchemy模型
"""

# 确保所有模型都被导入以建立正确的关系
from .base import BaseEntity
from .user import User
from .project import Project, ProjectStatus, TaskStatus, TaskType, ProjectType
from .document import Document, DocumentType, ProcessingStatus
from .conversation import Conversation, Message, MessageType
from .chunk import Chunk
from .memory import Memory, MemoryType, MemoryStatus, ProjectMemory, UserMemory, ConversationMemory
from .memory_schemas import *
from .analysis import DocumentAnalysis, AnalysisStatus
from .processing_pipeline import ProcessingPipeline, PipelineStage, ProcessingResult, StageStatus, ProcessingStage

__all__ = [
    # Base
    "BaseEntity",
    # User
    "User",
    # Project
    "Project", "ProjectStatus", "TaskStatus", "TaskType", "ProjectType",
    # Document
    "Document", "DocumentType", "ProcessingStatus",
    # Conversation
    "Conversation", "Message", "MessageType",
    # Chunk
    "Chunk",
    # Memory
    "Memory", "MemoryType", "MemoryStatus", "ProjectMemory", "UserMemory", "ConversationMemory",
    # Analysis
    "DocumentAnalysis", "AnalysisStatus",
    # Processing Pipeline
    "ProcessingPipeline", "PipelineStage", "ProcessingResult", "StageStatus", "ProcessingStage",
] 