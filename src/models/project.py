"""
项目相关数据模型
包含项目、研究计划、研究任务等实体的定义
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


class ProjectStatus(str, Enum):
    """项目状态枚举"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ResearchPhase(str, Enum):
    """研究阶段枚举"""
    PLANNING = "planning"
    LITERATURE_REVIEW = "literature_review"
    DATA_COLLECTION = "data_collection"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    WRITING = "writing"
    REVIEW = "review"
    COMPLETED = "completed"


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """任务优先级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# SQLAlchemy模型
class Project(BaseEntity):
    """项目实体"""
    __tablename__ = "projects"
    
    # 基本信息
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.ACTIVE)
    
    # 研究信息
    research_domain = Column(String(100), nullable=True)
    research_questions = Column(JSON, default=list)  # 研究问题列表
    research_objectives = Column(JSON, default=list)  # 研究目标列表
    current_phase = Column(SQLEnum(ResearchPhase), default=ResearchPhase.PLANNING)
    
    # 项目配置
    knowledge_base_config = Column(JSON, default=dict)
    retrieval_config = Column(JSON, default=dict)
    
    # 统计信息
    document_count = Column(Integer, default=0)
    total_chunks = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    
    # 关联信息
    owner_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    tags = Column(ARRAY(String), default=list)
    
    # 时间信息
    start_date = Column(String(20), nullable=True)
    target_end_date = Column(String(20), nullable=True)
    actual_end_date = Column(String(20), nullable=True)
    
    # 关系
    owner = relationship("User", back_populates="projects")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    research_plans = relationship("ResearchPlan", back_populates="project", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="project", cascade="all, delete-orphan")
    memory_entries = relationship("ProjectMemory", back_populates="project", cascade="all, delete-orphan")


class ResearchPlan(BaseEntity):
    """研究计划实体"""
    __tablename__ = "research_plans"
    
    # 基本信息
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    research_type = Column(String(50), nullable=False)  # exploratory, descriptive, explanatory
    
    # 计划结构
    research_questions = Column(JSON, default=list)
    methodology = Column(Text, nullable=True)
    expected_outcomes = Column(JSON, default=list)
    success_metrics = Column(JSON, default=list)
    
    # 时间规划
    estimated_duration_days = Column(Integer, nullable=True)
    planned_start_date = Column(String(20), nullable=True)
    planned_end_date = Column(String(20), nullable=True)
    
    # 资源需求
    required_documents = Column(JSON, default=list)
    required_tools = Column(JSON, default=list)
    dependencies = Column(JSON, default=list)
    
    # 执行状态
    current_phase = Column(SQLEnum(ResearchPhase), default=ResearchPhase.PLANNING)
    progress_percentage = Column(Float, default=0.0)
    
    # 关联信息
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    
    # 关系
    project = relationship("Project", back_populates="research_plans")
    tasks = relationship("ResearchTask", back_populates="research_plan", cascade="all, delete-orphan")


class ResearchTask(BaseEntity):
    """研究任务实体"""
    __tablename__ = "research_tasks"
    
    # 基本信息
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    task_type = Column(String(50), nullable=False)  # document_analysis, synthesis, validation
    
    # 任务状态
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM)
    
    # 任务内容
    instructions = Column(Text, nullable=True)
    expected_output = Column(Text, nullable=True)
    actual_output = Column(Text, nullable=True)
    
    # 时间信息
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, nullable=True)
    due_date = Column(String(20), nullable=True)
    completed_at = Column(String(20), nullable=True)
    
    # 依赖关系
    depends_on = Column(ARRAY(PG_UUID(as_uuid=True)), default=list)
    blocks = Column(ARRAY(PG_UUID(as_uuid=True)), default=list)
    
    # 资源和配置
    required_documents = Column(ARRAY(PG_UUID(as_uuid=True)), default=list)
    agent_config = Column(JSON, default=dict)
    
    # 关联信息
    research_plan_id = Column(PG_UUID(as_uuid=True), ForeignKey("research_plans.id"), nullable=False)
    assigned_agent = Column(String(100), nullable=True)
    
    # 关系
    research_plan = relationship("ResearchPlan", back_populates="tasks")


# Pydantic模式
class ProjectCreateSchema(BaseEntitySchema):
    """项目创建模式"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    research_domain: Optional[str] = Field(None, max_length=100)
    research_questions: List[str] = Field(default_factory=list)
    research_objectives: List[str] = Field(default_factory=list)
    knowledge_base_config: Dict[str, Any] = Field(default_factory=dict)
    retrieval_config: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    start_date: Optional[str] = None
    target_end_date: Optional[str] = None


class ProjectUpdateSchema(BaseEntitySchema):
    """项目更新模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    research_domain: Optional[str] = Field(None, max_length=100)
    research_questions: Optional[List[str]] = None
    research_objectives: Optional[List[str]] = None
    current_phase: Optional[ResearchPhase] = None
    knowledge_base_config: Optional[Dict[str, Any]] = None
    retrieval_config: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    target_end_date: Optional[str] = None
    actual_end_date: Optional[str] = None


class ProjectResponseSchema(BaseEntitySchema):
    """项目响应模式"""
    name: str
    description: Optional[str] = None
    status: ProjectStatus
    research_domain: Optional[str] = None
    research_questions: List[str]
    research_objectives: List[str]
    current_phase: ResearchPhase
    knowledge_base_config: Dict[str, Any]
    retrieval_config: Dict[str, Any]
    document_count: int
    total_chunks: int
    total_questions: int
    owner_id: UUID
    tags: List[str]
    start_date: Optional[str] = None
    target_end_date: Optional[str] = None
    actual_end_date: Optional[str] = None


class ResearchPlanCreateSchema(BaseEntitySchema):
    """研究计划创建模式"""
    title: str = Field(..., min_length=1, max_length=300)
    description: Optional[str] = None
    research_type: str = Field(..., min_length=1, max_length=50)
    research_questions: List[str] = Field(default_factory=list)
    methodology: Optional[str] = None
    expected_outcomes: List[str] = Field(default_factory=list)
    success_metrics: List[str] = Field(default_factory=list)
    estimated_duration_days: Optional[int] = Field(None, ge=1)
    planned_start_date: Optional[str] = None
    planned_end_date: Optional[str] = None
    required_documents: List[UUID] = Field(default_factory=list)
    required_tools: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    project_id: UUID


class ResearchPlanUpdateSchema(BaseEntitySchema):
    """研究计划更新模式"""
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    description: Optional[str] = None
    research_questions: Optional[List[str]] = None
    methodology: Optional[str] = None
    expected_outcomes: Optional[List[str]] = None
    success_metrics: Optional[List[str]] = None
    current_phase: Optional[ResearchPhase] = None
    progress_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    estimated_duration_days: Optional[int] = Field(None, ge=1)
    planned_start_date: Optional[str] = None
    planned_end_date: Optional[str] = None


class ResearchPlanResponseSchema(BaseEntitySchema):
    """研究计划响应模式"""
    title: str
    description: Optional[str] = None
    research_type: str
    research_questions: List[str]
    methodology: Optional[str] = None
    expected_outcomes: List[str]
    success_metrics: List[str]
    estimated_duration_days: Optional[int] = None
    planned_start_date: Optional[str] = None
    planned_end_date: Optional[str] = None
    required_documents: List[UUID]
    required_tools: List[str]
    dependencies: List[str]
    current_phase: ResearchPhase
    progress_percentage: float
    project_id: UUID


class ResearchTaskCreateSchema(BaseEntitySchema):
    """研究任务创建模式"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    task_type: str = Field(..., min_length=1, max_length=50)
    priority: TaskPriority = TaskPriority.MEDIUM
    instructions: Optional[str] = None
    expected_output: Optional[str] = None
    estimated_hours: Optional[float] = Field(None, ge=0.1)
    due_date: Optional[str] = None
    depends_on: List[UUID] = Field(default_factory=list)
    required_documents: List[UUID] = Field(default_factory=list)
    agent_config: Dict[str, Any] = Field(default_factory=dict)
    assigned_agent: Optional[str] = None
    research_plan_id: UUID


class ResearchTaskUpdateSchema(BaseEntitySchema):
    """研究任务更新模式"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    instructions: Optional[str] = None
    expected_output: Optional[str] = None
    actual_output: Optional[str] = None
    estimated_hours: Optional[float] = Field(None, ge=0.1)
    actual_hours: Optional[float] = Field(None, ge=0.1)
    due_date: Optional[str] = None
    completed_at: Optional[str] = None
    agent_config: Optional[Dict[str, Any]] = None
    assigned_agent: Optional[str] = None


class ResearchTaskResponseSchema(BaseEntitySchema):
    """研究任务响应模式"""
    title: str
    description: Optional[str] = None
    task_type: str
    status: TaskStatus
    priority: TaskPriority
    instructions: Optional[str] = None
    expected_output: Optional[str] = None
    actual_output: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    due_date: Optional[str] = None
    completed_at: Optional[str] = None
    depends_on: List[UUID]
    blocks: List[UUID]
    required_documents: List[UUID]
    agent_config: Dict[str, Any]
    assigned_agent: Optional[str] = None
    research_plan_id: UUID 