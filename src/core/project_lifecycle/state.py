"""
项目生命周期状态定义
"""

from typing import TypedDict, List, Dict, Any, Optional, Literal
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, field


class ProjectPhase(str, Enum):
    """项目阶段"""
    REQUIREMENTS = "requirements"  # 需求分析
    PLANNING = "planning"         # 计划制定
    EXECUTION = "execution"       # 执行实施
    RECORDING = "recording"       # 记录总结
    COMPLETION = "completion"     # 项目完成


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"           # 待处理
    READY = "ready"              # 就绪
    IN_PROGRESS = "in_progress"  # 进行中
    BLOCKED = "blocked"          # 阻塞
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"           # 失败
    CANCELLED = "cancelled"     # 已取消


class TaskType(str, Enum):
    """任务类型"""
    DATA_COLLECTION = "data_collection"    # 资料搜集
    DATA_INDEXING = "data_indexing"       # 资料索引
    DEEP_ANALYSIS = "deep_analysis"       # 深度分析
    VERIFICATION = "verification"         # 补充验证
    REPORT_WRITING = "report_writing"     # 报告撰写
    CUSTOM = "custom"                     # 自定义


@dataclass
class TaskDefinition:
    """任务定义"""
    id: str
    title: str
    description: str
    type: TaskType
    priority: int = 0
    
    # 执行计划
    estimated_time: Optional[int] = None  # 预计耗时（分钟）
    required_resources: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    # 质量要求
    quality_criteria: Dict[str, float] = field(default_factory=dict)
    output_format: Optional[str] = None
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskSnapshot:
    """任务快照"""
    task_id: str
    timestamp: datetime
    status: TaskStatus
    
    # 执行状态
    progress: float = 0.0  # 0-1
    context: Dict[str, Any] = field(default_factory=dict)
    decisions: List[Dict[str, Any]] = field(default_factory=list)
    
    # 中间结果
    intermediate_results: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    
    # 性能指标
    memory_usage: float = 0.0
    execution_time: float = 0.0


class ProjectState(TypedDict):
    """项目执行状态 - LangGraph状态定义"""
    # 项目标识
    project_id: str
    project_name: str
    project_type: str
    
    # 当前阶段
    current_phase: ProjectPhase
    phase_history: List[Dict[str, Any]]
    
    # 任务管理
    tasks: List[TaskDefinition]
    task_status: Dict[str, TaskStatus]  # task_id -> status
    active_tasks: List[str]
    completed_tasks: List[str]
    blocked_tasks: List[str]
    
    # 执行计划
    execution_plan: Dict[str, Any]
    task_dependencies: Dict[str, List[str]]  # task_id -> [dependency_ids]
    critical_path: List[str]
    
    # 项目上下文
    project_context: Dict[str, Any]
    user_preferences: Dict[str, Any]
    quality_gates: Dict[str, float]
    
    # 执行追踪
    execution_log: List[Dict[str, Any]]
    error_log: List[Dict[str, Any]]
    metrics: Dict[str, float]
    
    # 记忆系统接口
    working_memory: Dict[str, Any]
    task_memories: Dict[str, List[TaskSnapshot]]  # task_id -> snapshots
    project_insights: List[Dict[str, Any]]
    
    # 输出和结果
    deliverables: List[Dict[str, Any]]
    final_report: Optional[Dict[str, Any]]
    
    # 元数据
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]


class TaskState(TypedDict):
    """任务执行状态"""
    task_id: str
    task_definition: TaskDefinition
    status: TaskStatus
    
    # 执行上下文
    input_data: Dict[str, Any]
    working_context: Dict[str, Any]
    
    # 执行进度
    steps_completed: List[str]
    current_step: Optional[str]
    progress: float
    
    # 结果和输出
    results: Dict[str, Any]
    artifacts: List[Dict[str, Any]]
    quality_scores: Dict[str, float]
    
    # 错误和重试
    errors: List[Dict[str, Any]]
    retry_count: int
    max_retries: int
    
    # 时间追踪
    started_at: Optional[datetime]
    updated_at: datetime
    completed_at: Optional[datetime]
    
    # 资源使用
    tokens_used: int
    api_calls_made: int
    memory_snapshots: List[Dict[str, Any]]


def create_initial_project_state(
    project_id: str,
    project_name: str,
    project_type: str,
    context: Optional[Dict[str, Any]] = None
) -> ProjectState:
    """创建初始项目状态"""
    now = datetime.now()
    
    return ProjectState(
        # 项目标识
        project_id=project_id,
        project_name=project_name,
        project_type=project_type,
        
        # 当前阶段
        current_phase=ProjectPhase.REQUIREMENTS,
        phase_history=[],
        
        # 任务管理
        tasks=[],
        task_status={},
        active_tasks=[],
        completed_tasks=[],
        blocked_tasks=[],
        
        # 执行计划
        execution_plan={},
        task_dependencies={},
        critical_path=[],
        
        # 项目上下文
        project_context=context or {},
        user_preferences={},
        quality_gates={
            "accuracy": 0.8,
            "completeness": 0.9,
            "relevance": 0.85
        },
        
        # 执行追踪
        execution_log=[],
        error_log=[],
        metrics={},
        
        # 记忆系统
        working_memory={},
        task_memories={},
        project_insights=[],
        
        # 输出
        deliverables=[],
        final_report=None,
        
        # 元数据
        created_at=now,
        updated_at=now,
        metadata={}
    )


def create_initial_task_state(
    task_definition: TaskDefinition,
    input_data: Optional[Dict[str, Any]] = None
) -> TaskState:
    """创建初始任务状态"""
    return TaskState(
        task_id=task_definition.id,
        task_definition=task_definition,
        status=TaskStatus.PENDING,
        
        # 执行上下文
        input_data=input_data or {},
        working_context={},
        
        # 执行进度
        steps_completed=[],
        current_step=None,
        progress=0.0,
        
        # 结果
        results={},
        artifacts=[],
        quality_scores={},
        
        # 错误处理
        errors=[],
        retry_count=0,
        max_retries=3,
        
        # 时间
        started_at=None,
        updated_at=datetime.now(),
        completed_at=None,
        
        # 资源
        tokens_used=0,
        api_calls_made=0,
        memory_snapshots=[]
    )