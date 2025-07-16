"""
文档处理管道模型
支持分阶段处理和进度跟踪
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Float, Enum as SQLEnum, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from .base import BaseEntity


class StageStatus(str, enum.Enum):
    """处理阶段状态"""
    PENDING = "pending"          # 等待处理
    PROCESSING = "processing"    # 处理中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"           # 失败
    SKIPPED = "skipped"         # 跳过
    INTERRUPTED = "interrupted"  # 被中断


class ProcessingStage(str, enum.Enum):
    """处理阶段类型"""
    UPLOAD = "upload"            # 上传
    SUMMARY = "summary"          # 摘要生成
    INDEX = "index"              # 索引创建
    ANALYSIS = "analysis"        # 深度分析


class ProcessingPipeline(BaseEntity):
    """处理管道模型"""
    __tablename__ = "processing_pipelines"
    
    # 基础字段（不重复定义BaseEntity的字段）
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # 管道状态
    current_stage = Column(String(50), nullable=True)
    overall_progress = Column(Float, default=0.0)
    interrupted = Column(Boolean, default=False)
    completed = Column(Boolean, default=False)
    can_resume = Column(Boolean, default=True)
    
    # 处理选项
    processing_options = Column(JSONB, default={})
    
    # 时间戳（额外的）
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # 关系
    document = relationship("Document", back_populates="processing_pipelines")
    user = relationship("User", backref="processing_pipelines")
    stages = relationship("PipelineStage", back_populates="pipeline", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ProcessingPipeline(id={self.id}, document_id={self.document_id}, current_stage={self.current_stage})>"


class PipelineStage(BaseEntity):
    """管道阶段模型"""
    __tablename__ = "pipeline_stages"
    
    # 基础字段（不重复定义BaseEntity的字段）
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey("processing_pipelines.id"), nullable=False)
    
    # 阶段信息
    stage_type = Column(SQLEnum(ProcessingStage), nullable=False)
    stage_name = Column(String(100), nullable=False)
    status = Column(SQLEnum(StageStatus), default=StageStatus.PENDING)
    progress = Column(Integer, default=0)  # 0-100
    
    # 执行信息
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)  # 秒
    estimated_time = Column(Integer, nullable=True)  # 预估时间（秒）
    
    # 状态信息
    message = Column(Text, nullable=True)
    can_interrupt = Column(Boolean, default=True)
    
    # 结果和错误
    result = Column(JSONB, nullable=True)
    error = Column(Text, nullable=True)
    error_details = Column(JSONB, nullable=True)
    
    # 配置
    config = Column(JSONB, default={})
    
    # 关系
    pipeline = relationship("ProcessingPipeline", back_populates="stages")
    
    def __repr__(self):
        return f"<PipelineStage(id={self.id}, type={self.stage_type}, status={self.status})>"


class ProcessingResult(BaseEntity):
    """处理结果存储模型"""
    __tablename__ = "processing_results"
    
    # 基础字段（不重复定义BaseEntity的字段）
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    pipeline_id = Column(UUID(as_uuid=True), ForeignKey("processing_pipelines.id"), nullable=False)
    stage_id = Column(UUID(as_uuid=True), ForeignKey("pipeline_stages.id"), nullable=False)
    
    # 结果信息
    result_type = Column(String(50), nullable=False)  # summary, index, analysis
    format = Column(String(20), default="json")  # json, text, binary
    
    # 存储位置
    storage_path = Column(String(500), nullable=True)  # MinIO路径
    inline_content = Column(JSONB, nullable=True)  # 小结果直接存储
    
    # 元数据
    meta_data = Column(JSONB, default={})
    size = Column(Integer, nullable=True)  # 字节
    checksum = Column(String(64), nullable=True)  # SHA256
    
    # 时间戳（额外的）
    expires_at = Column(DateTime, nullable=True)  # 可选过期时间
    
    # 关系
    document = relationship("Document", backref="processing_results")
    
    def __repr__(self):
        return f"<ProcessingResult(id={self.id}, type={self.result_type}, document_id={self.document_id})>"