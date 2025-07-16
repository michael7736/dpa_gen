"""
分析相关的数据模型
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Float, JSON, ForeignKey, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from ..models.base import Base
from ..graphs.advanced_document_analyzer import AnalysisDepth, AnalysisStage


class AnalysisStatus(str, Enum):
    """分析状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# SQLAlchemy模型
class DocumentAnalysis(Base):
    """文档分析记录"""
    __tablename__ = "document_analyses"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(PGUUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    user_id = Column(String, nullable=False)
    
    # 分析配置
    analysis_depth = Column(String, default=AnalysisDepth.STANDARD)
    analysis_goal = Column(Text, nullable=True)
    
    # 状态跟踪
    status = Column(String, default=AnalysisStatus.PENDING)
    current_stage = Column(String, nullable=True)
    progress = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    
    # 时间记录
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    processing_time_seconds = Column(Float, nullable=True)
    
    # 结果存储
    executive_summary = Column(Text, nullable=True)
    key_insights = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    quality_score = Column(Float, nullable=True)
    
    # 详细结果（存储为JSON）
    detailed_report = Column(JSON, nullable=True)
    visualization_data = Column(JSON, nullable=True)
    action_plan = Column(JSON, nullable=True)
    
    # 关系
    document = relationship("Document", back_populates="analyses")
    # project = relationship("Project", back_populates="analyses")


# Pydantic模型
class AnalysisRequest(BaseModel):
    """分析请求"""
    document_id: UUID
    project_id: UUID
    analysis_depth: AnalysisDepth = AnalysisDepth.STANDARD
    analysis_goal: Optional[str] = None


class AnalysisResponse(BaseModel):
    """分析响应"""
    analysis_id: UUID
    status: AnalysisStatus
    message: str
    estimated_time: Optional[int] = None  # 预计时间（秒）


class AnalysisStatusModel(BaseModel):
    """分析状态"""
    analysis_id: UUID
    document_id: UUID
    status: AnalysisStatus
    current_stage: Optional[str] = None
    progress: float = 0.0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None


class AnalysisResult(BaseModel):
    """分析结果"""
    analysis_id: UUID
    document_id: UUID
    project_id: UUID
    status: AnalysisStatus
    analysis_depth: AnalysisDepth
    
    # 核心结果
    executive_summary: Optional[str] = None
    key_insights: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    quality_score: Optional[float] = None
    
    # 详细结果
    detailed_report: Optional[Dict[str, Any]] = None
    visualization_data: Optional[Dict[str, Any]] = None
    action_plan: Optional[Dict[str, Any]] = None
    
    # 元数据
    created_at: datetime
    completed_at: Optional[datetime] = None
    processing_time_seconds: Optional[float] = None


class QuickAnalysisRequest(BaseModel):
    """快速分析请求（直接提供文本）"""
    content: str
    title: Optional[str] = "Quick Analysis"
    analysis_depth: AnalysisDepth = AnalysisDepth.BASIC
    analysis_goal: Optional[str] = None


class AnalysisListResponse(BaseModel):
    """分析列表响应"""
    analyses: List[AnalysisStatusModel]
    total: int
    page: int = 1
    per_page: int = 20