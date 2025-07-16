"""
项目相关的数据模型 - 支持半自动DPA的项目生命周期管理
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Float, Enum as SQLEnum, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship, backref
from datetime import datetime
import uuid
import enum

from .base import BaseEntity


class ProjectType(str, enum.Enum):
    """项目类型"""
    RESEARCH = "research"              # 研究项目
    ANALYSIS = "analysis"              # 分析项目
    REPORT = "report"                  # 报告项目
    DOCUMENTATION = "documentation"    # 文档项目
    CUSTOM = "custom"                  # 自定义项目


class ProjectStatus(str, enum.Enum):
    """项目状态"""
    DRAFT = "draft"                   # 草稿
    PLANNING = "planning"             # 规划中
    EXECUTING = "executing"           # 执行中
    PAUSED = "paused"                # 已暂停
    COMPLETED = "completed"           # 已完成
    ARCHIVED = "archived"             # 已归档
    CANCELLED = "cancelled"           # 已取消


class TaskType(str, enum.Enum):
    """任务类型"""
    DATA_COLLECTION = "data_collection"    # 资料搜集
    DATA_INDEXING = "data_indexing"       # 资料索引
    DEEP_ANALYSIS = "deep_analysis"       # 深度分析
    VERIFICATION = "verification"         # 补充验证
    REPORT_WRITING = "report_writing"     # 报告撰写
    CUSTOM = "custom"                     # 自定义


class TaskStatus(str, enum.Enum):
    """任务状态"""
    PENDING = "pending"           # 待处理
    READY = "ready"              # 就绪
    IN_PROGRESS = "in_progress"  # 进行中
    BLOCKED = "blocked"          # 阻塞
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"           # 失败
    CANCELLED = "cancelled"     # 已取消


class Project(BaseEntity):
    """项目模型"""
    __tablename__ = "projects"
    
    # 基础字段
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    type = Column(SQLEnum(ProjectType), default=ProjectType.RESEARCH)
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.DRAFT, index=True)
    is_default = Column(Boolean, default=False, index=True)  # 是否为默认项目
    
    # 项目配置
    config = Column(JSONB, default={})
    template_id = Column(UUID(as_uuid=True), ForeignKey("project_templates.id"), nullable=True)
    quality_gates = Column(JSONB, default={
        "accuracy": 0.8,
        "completeness": 0.9,
        "relevance": 0.85
    })
    
    # 项目上下文
    context = Column(JSONB, default={})
    objectives = Column(ARRAY(Text), default=[])
    constraints = Column(ARRAY(Text), default=[])
    
    # 执行计划
    execution_plan = Column(JSONB, default={})
    estimated_duration = Column(Integer)  # 分钟
    actual_duration = Column(Integer)     # 分钟
    
    # 项目指标
    progress = Column(Float, default=0.0)
    quality_score = Column(Float, default=0.0)
    success_rate = Column(Float, default=0.0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # 用户关系
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # 关系
    user = relationship("User", back_populates="projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    memories = relationship("ProjectMemory", back_populates="project", cascade="all, delete-orphan")
    deliverables = relationship("Deliverable", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(id={self.id}, name={self.name}, status={self.status})>"


class Task(BaseEntity):
    """任务模型"""
    __tablename__ = "tasks"
    
    # 基础字段
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True)
    
    title = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(SQLEnum(TaskType), default=TaskType.CUSTOM)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, index=True)
    priority = Column(Integer, default=0)
    order = Column(Integer, default=0)
    
    # 执行计划
    plan = Column(JSONB, default={})
    dependencies = Column(ARRAY(UUID(as_uuid=True)), default=[])
    estimated_time = Column(Integer)  # 分钟
    actual_time = Column(Integer)     # 分钟
    
    # 执行结果
    result = Column(JSONB, default={})
    artifacts = Column(JSONB, default=[])
    quality_criteria = Column(JSONB, default={})
    quality_score = Column(Float)
    
    # 错误处理
    error_count = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    last_error = Column(Text)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # 关系
    project = relationship("Project", back_populates="tasks")
    parent = relationship("Task", remote_side=[id], backref="children")
    snapshots = relationship("TaskSnapshot", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Task(id={self.id}, title={self.title}, status={self.status})>"


class TaskSnapshot(BaseEntity):
    """任务快照模型"""
    __tablename__ = "task_snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    
    # 快照信息
    status = Column(SQLEnum(TaskStatus), nullable=False)
    progress = Column(Float, default=0.0)
    context = Column(JSONB, default={})
    decisions = Column(JSONB, default=[])
    intermediate_results = Column(JSONB, default={})
    
    # 性能指标
    memory_usage = Column(Float)
    execution_time = Column(Float)
    tokens_used = Column(Integer, default=0)
    api_calls = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系
    task = relationship("Task", back_populates="snapshots")
    
    def __repr__(self):
        return f"<TaskSnapshot(id={self.id}, task_id={self.task_id}, status={self.status})>"


class ProjectMemory(BaseEntity):
    """项目记忆模型"""
    __tablename__ = "project_memories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    
    # 记忆内容
    memory_type = Column(String(50), nullable=False)  # working, task, project
    content = Column(JSONB, nullable=False)
    
    # 知识图谱
    knowledge_graph = Column(JSONB, default={})
    entities = Column(JSONB, default=[])
    relationships = Column(JSONB, default=[])
    
    # 洞察和模式
    insights = Column(JSONB, default=[])
    patterns = Column(JSONB, default=[])
    learnings = Column(JSONB, default=[])
    
    # 元数据
    meta_data = Column(JSONB, default={})
    ttl = Column(Integer)  # 生存时间（秒）
    expires_at = Column(DateTime)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    project = relationship("Project", back_populates="memories")
    
    def __repr__(self):
        return f"<ProjectMemory(id={self.id}, project_id={self.project_id}, type={self.memory_type})>"


class Deliverable(BaseEntity):
    """可交付成果模型"""
    __tablename__ = "deliverables"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    
    # 成果信息
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # report, dataset, analysis, etc.
    format = Column(String(50))  # pdf, json, csv, etc.
    
    # 内容
    content = Column(JSONB, default={})
    file_path = Column(String(500))
    file_size = Column(Integer)
    
    # 质量和版本
    version = Column(String(50), default="1.0")
    quality_score = Column(Float)
    is_final = Column(Boolean, default=False)
    
    # 元数据
    meta_data = Column(JSONB, default={})
    tags = Column(ARRAY(String), default=[])
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    project = relationship("Project", back_populates="deliverables")
    
    def __repr__(self):
        return f"<Deliverable(id={self.id}, name={self.name}, type={self.type})>"


class ProjectTemplate(BaseEntity):
    """项目模板模型"""
    __tablename__ = "project_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 模板信息
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    category = Column(String(100))
    
    # 模板内容
    project_type = Column(SQLEnum(ProjectType), default=ProjectType.CUSTOM)
    default_tasks = Column(JSONB, default=[])
    default_workflow = Column(JSONB, default={})
    default_config = Column(JSONB, default={})
    
    # 使用统计
    usage_count = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    
    # 元数据
    is_public = Column(Boolean, default=True)
    tags = Column(ARRAY(String), default=[])
    meta_data = Column(JSONB, default={})
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 创建者
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    def __repr__(self):
        return f"<ProjectTemplate(id={self.id}, name={self.name})>"


 