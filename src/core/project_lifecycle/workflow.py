"""
项目生命周期工作流定义
基于LangGraph构建的状态机
"""

from typing import Dict, Any, Optional, List, Callable
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from .state import ProjectState, ProjectPhase, TaskStatus
from .nodes import (
    analyze_requirements,
    create_plan,
    validate_plan,
    execute_task,
    monitor_progress,
    evaluate_quality,
    record_results,
    complete_project
)
from ...utils.logger import get_logger

logger = get_logger(__name__)


class ProjectWorkflow:
    """项目工作流管理器"""
    
    def __init__(self, checkpointer: Optional[Any] = None):
        self.checkpointer = checkpointer or MemorySaver()
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """构建项目工作流"""
        workflow = StateGraph(ProjectState)
        
        # 添加所有节点
        workflow.add_node("analyze_requirements", analyze_requirements)
        workflow.add_node("create_plan", create_plan)
        workflow.add_node("validate_plan", validate_plan)
        workflow.add_node("execute_task", execute_task)
        workflow.add_node("monitor_progress", monitor_progress)
        workflow.add_node("evaluate_quality", evaluate_quality)
        workflow.add_node("record_results", record_results)
        workflow.add_node("complete_project", complete_project)
        
        # 定义流程边
        workflow.add_edge(START, "analyze_requirements")
        workflow.add_edge("analyze_requirements", "create_plan")
        workflow.add_edge("create_plan", "validate_plan")
        
        # 验证计划后的条件跳转
        workflow.add_conditional_edges(
            "validate_plan",
            self._should_proceed_to_execution,
            {
                "execute": "execute_task",
                "replan": "create_plan",
                "complete": "complete_project"
            }
        )
        
        # 执行任务后监控进度
        workflow.add_edge("execute_task", "monitor_progress")
        
        # 监控后的条件跳转
        workflow.add_conditional_edges(
            "monitor_progress",
            self._determine_next_action,
            {
                "continue": "execute_task",
                "evaluate": "evaluate_quality",
                "complete": "complete_project",
                "error": "record_results"
            }
        )
        
        # 质量评估后记录
        workflow.add_edge("evaluate_quality", "record_results")
        
        # 记录后的条件跳转
        workflow.add_conditional_edges(
            "record_results",
            self._should_continue_execution,
            {
                "continue": "execute_task",
                "complete": "complete_project"
            }
        )
        
        # 完成项目
        workflow.add_edge("complete_project", END)
        
        return workflow.compile(checkpointer=self.checkpointer)
    
    def _should_proceed_to_execution(self, state: ProjectState) -> str:
        """判断是否应该继续执行"""
        # 检查是否有任务
        if not state.get("tasks"):
            logger.warning("No tasks found in plan")
            return "replan"
        
        # 检查计划质量
        plan_quality = state.get("metrics", {}).get("plan_quality", 0)
        if plan_quality < 0.6:
            logger.info(f"Plan quality too low: {plan_quality}")
            return "replan"
        
        # 检查是否所有任务都已完成
        all_completed = all(
            state["task_status"].get(task.id) == TaskStatus.COMPLETED
            for task in state["tasks"]
        )
        if all_completed:
            return "complete"
        
        return "execute"
    
    def _determine_next_action(self, state: ProjectState) -> str:
        """决定下一步动作"""
        # 检查错误
        if state.get("error_log"):
            recent_errors = [e for e in state["error_log"] if e.get("critical")]
            if recent_errors:
                logger.error(f"Critical errors found: {len(recent_errors)}")
                return "error"
        
        # 检查是否需要质量评估
        completed_count = len(state.get("completed_tasks", []))
        if completed_count > 0 and completed_count % 3 == 0:  # 每3个任务评估一次
            return "evaluate"
        
        # 检查是否还有待执行的任务
        pending_tasks = [
            task_id for task_id, status in state.get("task_status", {}).items()
            if status in [TaskStatus.PENDING, TaskStatus.READY]
        ]
        
        if not pending_tasks:
            # 检查是否有阻塞的任务
            if state.get("blocked_tasks"):
                logger.warning(f"Blocked tasks found: {state['blocked_tasks']}")
                return "error"
            return "complete"
        
        return "continue"
    
    def _should_continue_execution(self, state: ProjectState) -> str:
        """判断是否继续执行"""
        # 检查是否所有任务完成
        all_tasks_done = all(
            status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
            for status in state.get("task_status", {}).values()
        )
        
        if all_tasks_done:
            return "complete"
        
        # 检查是否达到最大错误数
        error_count = len(state.get("error_log", []))
        if error_count > 10:  # 可配置的阈值
            logger.error("Too many errors, completing project")
            return "complete"
        
        return "continue"
    
    async def execute(
        self,
        initial_state: ProjectState,
        config: Optional[Dict[str, Any]] = None
    ) -> ProjectState:
        """执行工作流"""
        logger.info(f"Starting project workflow for: {initial_state['project_id']}")
        
        # 配置
        config = config or {}
        thread_id = config.get("thread_id", initial_state["project_id"])
        
        # 执行工作流
        final_state = await self.workflow.ainvoke(
            initial_state,
            config={"configurable": {"thread_id": thread_id}}
        )
        
        logger.info(f"Project workflow completed: {final_state['current_phase']}")
        return final_state
    
    def get_state(self, thread_id: str) -> Optional[ProjectState]:
        """获取工作流状态"""
        checkpoint = self.checkpointer.get(
            config={"configurable": {"thread_id": thread_id}}
        )
        return checkpoint.get("state") if checkpoint else None
    
    def get_history(self, thread_id: str) -> List[ProjectState]:
        """获取工作流历史"""
        history = []
        for checkpoint in self.checkpointer.list(
            config={"configurable": {"thread_id": thread_id}}
        ):
            history.append(checkpoint["state"])
        return history


def create_project_workflow(
    checkpointer: Optional[Any] = None
) -> ProjectWorkflow:
    """创建项目工作流实例"""
    return ProjectWorkflow(checkpointer)


# 条件函数
def should_retry_task(state: ProjectState) -> bool:
    """判断是否应该重试任务"""
    current_task_id = state.get("active_tasks", [None])[0]
    if not current_task_id:
        return False
    
    task_state = state.get("task_memories", {}).get(current_task_id, [])
    if not task_state:
        return False
    
    latest_snapshot = task_state[-1]
    return (
        latest_snapshot.get("status") == TaskStatus.FAILED and
        latest_snapshot.get("retry_count", 0) < 3
    )


def should_escalate_error(state: ProjectState) -> bool:
    """判断是否应该上报错误"""
    error_log = state.get("error_log", [])
    critical_errors = [e for e in error_log if e.get("severity") == "critical"]
    
    return len(critical_errors) > 0 or len(error_log) > 5


def calculate_project_progress(state: ProjectState) -> float:
    """计算项目进度"""
    total_tasks = len(state.get("tasks", []))
    if total_tasks == 0:
        return 0.0
    
    completed_tasks = len(state.get("completed_tasks", []))
    return completed_tasks / total_tasks