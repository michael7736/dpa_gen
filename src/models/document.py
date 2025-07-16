"""
文档相关数据模型
包含文档、章节、块等实体的定义
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, Enum as SQLEnum, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ARRAY
from sqlalchemy.orm import relationship
from pydantic import Field, validator

from .base import BaseEntity, BaseEntitySchema


class DocumentType(str, Enum):
    """文档类型枚举"""
    PDF = "pdf"
    WORD = "word"
    MARKDOWN = "markdown"
    TEXT = "text"
    HTML = "html"
    RESEARCH_PAPER = "research_paper"
    MANUAL = "manual"
    REPORT = "report"


class ProcessingStatus(str, Enum):
    """处理状态枚举"""
    UPLOADED = "uploaded"        # 已上传（新增）
    PENDING = "pending"          # 待处理
    PROCESSING = "processing"    # 处理中
    SUMMARIZING = "summarizing"  # 正在生成摘要（新增）
    SUMMARIZED = "summarized"    # 已生成摘要（新增）
    INDEXING = "indexing"        # 正在索引（新增）
    INDEXED = "indexed"          # 已索引（新增）
    ANALYZING = "analyzing"      # 正在分析（新增）
    ANALYZED = "analyzed"        # 已分析（新增）
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"           # 失败
    CANCELLED = "cancelled"     # 已取消


class ChunkType(str, Enum):
    """块类型枚举"""
    TITLE = "title"
    SECTION = "section"
    PARAGRAPH = "paragraph"
    LIST = "list"
    TABLE = "table"
    FIGURE = "figure"
    CODE = "code"
    FORMULA = "formula"


# SQLAlchemy模型
class Document(BaseEntity):
    """文档实体"""
    __tablename__ = "documents"
    
    # 基本信息
    title = Column(String(500), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False, unique=True)
    
    # 文档类型和状态
    document_type = Column(SQLEnum(DocumentType), nullable=False)
    processing_status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.PENDING)
    
    # 内容信息
    content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    language = Column(String(10), default="zh", nullable=False)
    page_count = Column(Integer, default=0)
    word_count = Column(Integer, default=0)
    
    # 结构化信息
    table_of_contents = Column(JSON, default=list)
    structure_tree = Column(JSON, default=dict)
    
    # 关联信息
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    author = Column(String(255), nullable=True)
    publication_date = Column(String(20), nullable=True)
    tags = Column(ARRAY(String), default=list)
    
    # 处理配置
    chunk_size = Column(Integer, default=1000)
    chunk_overlap = Column(Integer, default=200)
    
    # 关系
    project = relationship("Project", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    sections = relationship("DocumentSection", back_populates="document", cascade="all, delete-orphan")
    analyses = relationship("DocumentAnalysis", back_populates="document", cascade="all, delete-orphan")
    processing_pipelines = relationship("ProcessingPipeline", back_populates="document", cascade="all, delete-orphan")
    # document_metadata = relationship("DocumentMetadata", back_populates="document", uselist=False, cascade="all, delete-orphan")


class DocumentSection(BaseEntity):
    """文档章节实体"""
    __tablename__ = "document_sections"
    
    # 基本信息
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)
    section_type = Column(String(50), nullable=False)  # chapter, section, subsection, etc.
    
    # 层次结构
    level = Column(Integer, nullable=False, default=1)
    parent_id = Column(PG_UUID(as_uuid=True), ForeignKey("document_sections.id"), nullable=True)
    order_index = Column(Integer, nullable=False, default=0)
    
    # 位置信息
    page_start = Column(Integer, nullable=True)
    page_end = Column(Integer, nullable=True)
    char_start = Column(Integer, nullable=True)
    char_end = Column(Integer, nullable=True)
    
    # 统计信息
    word_count = Column(Integer, default=0)
    
    # 关联信息
    document_id = Column(PG_UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    
    # 关系
    document = relationship("Document", back_populates="sections")
    parent = relationship("DocumentSection", remote_side="DocumentSection.id")
    children = relationship("DocumentSection", back_populates="parent")
    # chunks = relationship("DocumentChunk", back_populates="section")  # Using Chunk from chunk.py instead


# Moved to chunk.py - using Chunk model instead
# class DocumentChunk(BaseEntity):
#     """文档块实体"""
#     __tablename__ = "document_chunks"
#     
#     # 基本信息
#     content = Column(Text, nullable=False)
#     chunk_type = Column(SQLEnum(ChunkType), default=ChunkType.PARAGRAPH)
#     
#     # 位置信息
#     chunk_index = Column(Integer, nullable=False)
#     page_number = Column(Integer, nullable=True)
#     char_start = Column(Integer, nullable=True)
#     char_end = Column(Integer, nullable=True)
#     
#     # 统计信息
#     word_count = Column(Integer, default=0)
#     token_count = Column(Integer, default=0)
#     
#     # 向量信息
#     embedding_vector = Column(ARRAY(Float), nullable=True)
#     embedding_model = Column(String(100), nullable=True)
#     
#     # 语义信息
#     semantic_similarity_score = Column(Float, nullable=True)
#     keywords = Column(ARRAY(String), default=list)
#     entities = Column(JSON, default=list)
#     
#     # 关联信息
#     document_id = Column(PG_UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
#     section_id = Column(PG_UUID(as_uuid=True), ForeignKey("document_sections.id"), nullable=True)
#     
#     # 关系
#     document = relationship("Document", back_populates="chunks")
#     section = relationship("DocumentSection", back_populates="chunks")

# Using Chunk from chunk.py instead
from .chunk import Chunk as DocumentChunk


# Pydantic模式
class DocumentCreateSchema(BaseEntitySchema):
    """文档创建模式"""
    title: str = Field(..., min_length=1, max_length=500)
    filename: str = Field(..., min_length=1, max_length=255)
    file_path: str = Field(..., min_length=1, max_length=1000)
    document_type: DocumentType
    project_id: UUID
    author: Optional[str] = Field(None, max_length=255)
    publication_date: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    chunk_size: int = Field(default=1000, ge=100, le=4000)
    chunk_overlap: int = Field(default=200, ge=0, le=1000)


class DocumentUpdateSchema(BaseEntitySchema):
    """文档更新模式"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    author: Optional[str] = Field(None, max_length=255)
    publication_date: Optional[str] = None
    tags: Optional[List[str]] = None
    summary: Optional[str] = None
    chunk_size: Optional[int] = Field(None, ge=100, le=4000)
    chunk_overlap: Optional[int] = Field(None, ge=0, le=1000)


class DocumentResponseSchema(BaseEntitySchema):
    """文档响应模式"""
    title: str
    filename: str
    file_size: int
    file_hash: str
    document_type: DocumentType
    processing_status: ProcessingStatus
    content: Optional[str] = None
    summary: Optional[str] = None
    language: str
    page_count: int
    word_count: int
    table_of_contents: List[Dict[str, Any]]
    structure_tree: Dict[str, Any]
    project_id: UUID
    author: Optional[str] = None
    publication_date: Optional[str] = None
    tags: List[str]
    chunk_size: int
    chunk_overlap: int


class DocumentSectionCreateSchema(BaseEntitySchema):
    """文档章节创建模式"""
    title: str = Field(..., min_length=1, max_length=500)
    content: Optional[str] = None
    section_type: str = Field(..., min_length=1, max_length=50)
    level: int = Field(default=1, ge=1, le=10)
    parent_id: Optional[UUID] = None
    order_index: int = Field(default=0, ge=0)
    page_start: Optional[int] = Field(None, ge=1)
    page_end: Optional[int] = Field(None, ge=1)
    char_start: Optional[int] = Field(None, ge=0)
    char_end: Optional[int] = Field(None, ge=0)
    document_id: UUID


class DocumentSectionResponseSchema(BaseEntitySchema):
    """文档章节响应模式"""
    title: str
    content: Optional[str] = None
    section_type: str
    level: int
    parent_id: Optional[UUID] = None
    order_index: int
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    word_count: int
    document_id: UUID


class DocumentChunkCreateSchema(BaseEntitySchema):
    """文档块创建模式"""
    content: str = Field(..., min_length=1)
    chunk_type: ChunkType = ChunkType.PARAGRAPH
    chunk_index: int = Field(..., ge=0)
    page_number: Optional[int] = Field(None, ge=1)
    char_start: Optional[int] = Field(None, ge=0)
    char_end: Optional[int] = Field(None, ge=0)
    keywords: List[str] = Field(default_factory=list)
    entities: List[Dict[str, Any]] = Field(default_factory=list)
    document_id: UUID
    section_id: Optional[UUID] = None


class DocumentChunkResponseSchema(BaseEntitySchema):
    """文档块响应模式"""
    content: str
    chunk_type: ChunkType
    chunk_index: int
    page_number: Optional[int] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    word_count: int
    token_count: int
    embedding_model: Optional[str] = None
    semantic_similarity_score: Optional[float] = None
    keywords: List[str]
    entities: List[Dict[str, Any]]
    document_id: UUID
    section_id: Optional[UUID] = None


class DocumentProcessingResultSchema(BaseEntitySchema):
    """文档处理结果模式"""
    document_id: UUID
    processing_status: ProcessingStatus
    total_chunks: int
    total_sections: int
    processing_time: float
    error_message: Optional[str] = None
    warnings: List[str] = Field(default_factory=list) 