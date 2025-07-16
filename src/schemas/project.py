"""
项目相关的Pydantic模式定义
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from ..models.project import ProjectType, ProjectStatus, TaskType, TaskStatus


# 项目相关模式

class ProjectCreateRequest(BaseModel):
    """创建项目请求"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    type: ProjectType = ProjectType.RESEARCH
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    objectives: Optional[List[str]] = Field(default_factory=list)
    constraints: Optional[List[str]] = Field(default_factory=list)


class ProjectUpdateRequest(BaseModel):
    """更新项目请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    config: Optional[Dict[str, Any]] = None
    objectives: Optional[List[str]] = None
    constraints: Optional[List[str]] = None
    quality_gates: Optional[Dict[str, float]] = None


class ProjectResponse(BaseModel):
    """项目响应"""
    id: UUID
    name: str
    description: Optional[str]
    type: ProjectType
    status: ProjectStatus
    config: Dict[str, Any]
    objectives: List[str]
    constraints: List[str]
    quality_gates: Dict[str, float]
    progress: float
    quality_score: float
    success_rate: float
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    user_id: UUID
    
    class Config:
        orm_mode = True
        from_attributes = True


# 任务相关模式

class TaskCreateRequest(BaseModel):
    """创建任务请求"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    type: TaskType = TaskType.CUSTOM
    priority: int = Field(0, ge=0, le=10)
    parent_id: Optional[UUID] = None
    dependencies: Optional[List[UUID]] = Field(default_factory=list)
    estimated_time: Optional[int] = Field(None, ge=1)  # 分钟
    plan: Optional[Dict[str, Any]] = Field(default_factory=dict)
    quality_criteria: Optional[Dict[str, float]] = Field(default_factory=dict)


class TaskUpdateRequest(BaseModel):
    """更新任务请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[int] = Field(None, ge=0, le=10)
    dependencies: Optional[List[UUID]] = None
    estimated_time: Optional[int] = Field(None, ge=1)
    actual_time: Optional[int] = Field(None, ge=0)
    plan: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    quality_score: Optional[float] = Field(None, ge=0, le=1)
    last_error: Optional[str] = None


class TaskResponse(BaseModel):
    """任务响应"""
    id: UUID
    project_id: UUID
    parent_id: Optional[UUID]
    title: str
    description: Optional[str]
    type: TaskType
    status: TaskStatus
    priority: int
    order: int
    dependencies: List[UUID]
    estimated_time: Optional[int]
    actual_time: Optional[int]
    plan: Dict[str, Any]
    result: Dict[str, Any]
    artifacts: List[Dict[str, Any]]
    quality_criteria: Dict[str, float]
    quality_score: Optional[float]
    error_count: int
    retry_count: int
    last_error: Optional[str]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        orm_mode = True
        from_attributes = True


# 任务快照模式

class TaskSnapshotResponse(BaseModel):
    """任务快照响应"""
    id: UUID
    task_id: UUID
    status: TaskStatus
    progress: float
    context: Dict[str, Any]
    decisions: List[Dict[str, Any]]
    intermediate_results: Dict[str, Any]
    memory_usage: Optional[float]
    execution_time: Optional[float]
    tokens_used: int
    api_calls: int
    created_at: datetime
    
    class Config:
        orm_mode = True
        from_attributes = True


# 项目记忆模式

class ProjectMemoryRequest(BaseModel):
    """项目记忆请求"""
    memory_type: str = Field(..., max_length=50)
    content: Dict[str, Any]
    knowledge_graph: Optional[Dict[str, Any]] = Field(default_factory=dict)
    entities: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    relationships: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    insights: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    patterns: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    ttl: Optional[int] = Field(None, ge=1)  # 秒


class ProjectMemoryResponse(BaseModel):
    """项目记忆响应"""
    id: UUID
    project_id: UUID
    memory_type: str
    content: Dict[str, Any]
    knowledge_graph: Dict[str, Any]
    entities: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    insights: List[Dict[str, Any]]
    patterns: List[Dict[str, Any]]
    learnings: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    ttl: Optional[int]
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
        from_attributes = True


# 可交付成果模式

class DeliverableRequest(BaseModel):
    """可交付成果请求"""
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., max_length=50)
    format: Optional[str] = Field(None, max_length=50)
    content: Dict[str, Any]
    file_path: Optional[str] = Field(None, max_length=500)
    version: Optional[str] = Field("1.0", max_length=50)
    quality_score: Optional[float] = Field(None, ge=0, le=1)
    is_final: bool = False
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tags: Optional[List[str]] = Field(default_factory=list)


class DeliverableResponse(BaseModel):
    """可交付成果响应"""
    id: UUID
    project_id: UUID
    name: str
    type: str
    format: Optional[str]
    content: Dict[str, Any]
    file_path: Optional[str]
    file_size: Optional[int]
    version: str
    quality_score: Optional[float]
    is_final: bool
    metadata: Dict[str, Any]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
        from_attributes = True


# 项目执行相关模式

class ProjectExecutionRequest(BaseModel):
    """项目执行请求"""
    initial_context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    user_preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)
    quality_gates: Optional[Dict[str, float]] = None


class ProjectExecutionResponse(BaseModel):
    """项目执行响应"""
    project_id: UUID
    execution_id: str
    status: str
    message: str
    current_phase: Optional[str]
    progress: float
    active_tasks: List[str]
    completed_tasks: List[str]
    metrics: Dict[str, float]


# 项目统计模式

class ProjectStatisticsResponse(BaseModel):
    """项目统计响应"""
    project_id: UUID
    project_name: str
    status: ProjectStatus
    task_statistics: Dict[str, int]  # pending, in_progress, completed, failed, etc.
    memory_statistics: Dict[str, int]  # working, task, project counts
    deliverable_count: int
    total_duration: Optional[int]  # 分钟
    quality_metrics: Dict[str, float]
    last_activity: Optional[datetime]