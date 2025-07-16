"""
项目生命周期工作流节点实现
每个节点负责特定的项目执行阶段
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from .state import ProjectState, ProjectPhase, TaskStatus, TaskType, TaskDefinition
from ...utils.logger import get_logger
from ...config.settings import get_settings

logger = get_logger(__name__)


async def analyze_requirements(state: ProjectState) -> Dict[str, Any]:
    """
    需求分析节点
    分析项目目标，识别关键需求，生成初步任务框架
    """
    logger.info(f"Analyzing requirements for project: {state['project_id']}")
    
    # 更新阶段
    state["current_phase"] = ProjectPhase.REQUIREMENTS
    state["phase_history"].append({
        "phase": ProjectPhase.REQUIREMENTS,
        "started_at": datetime.now(),
        "status": "in_progress"
    })
    
    # 获取项目上下文
    project_context = state.get("project_context", {})
    project_type = state.get("project_type", "research")
    
    try:
        # 使用LLM分析需求
        settings = get_settings()
        if settings.ai_model.openai_api_key:
            llm = ChatOpenAI(
                model="gpt-4o",
                temperature=0.3,
                openai_api_key=settings.ai_model.openai_api_key
            )
            
            analysis_prompt = f"""
分析以下项目需求，识别关键任务和目标：

项目名称：{state['project_name']}
项目类型：{project_type}
项目背景：{json.dumps(project_context, ensure_ascii=False)}

请返回JSON格式的分析结果：
{{
    "main_objectives": ["目标1", "目标2", ...],
    "key_requirements": ["需求1", "需求2", ...],
    "suggested_tasks": [
        {{"title": "任务标题", "type": "任务类型", "description": "任务描述", "priority": 1-5}}
    ],
    "constraints": ["约束1", "约束2", ...],
    "success_criteria": {{"criterion": "target_value"}}
}}
"""
            
            response = await llm.ainvoke([HumanMessage(content=analysis_prompt)])
            analysis_result = json.loads(response.content)
        else:
            # 模拟模式
            analysis_result = {
                "main_objectives": [
                    f"完成{project_type}项目的主要目标",
                    "生成高质量的研究报告"
                ],
                "key_requirements": [
                    "收集相关资料",
                    "深度分析数据",
                    "生成洞察报告"
                ],
                "suggested_tasks": [
                    {
                        "title": "收集项目相关资料",
                        "type": "data_collection",
                        "description": "搜集和整理项目所需的所有资料",
                        "priority": 5
                    },
                    {
                        "title": "资料索引和整理",
                        "type": "data_indexing", 
                        "description": "对收集的资料进行索引和结构化整理",
                        "priority": 4
                    },
                    {
                        "title": "深度分析",
                        "type": "deep_analysis",
                        "description": "对资料进行深度分析，提取关键洞察",
                        "priority": 3
                    }
                ],
                "constraints": ["时间限制", "资源限制"],
                "success_criteria": {
                    "accuracy": 0.85,
                    "completeness": 0.9
                }
            }
        
        # 更新状态
        state["project_context"].update({
            "requirements_analysis": analysis_result,
            "analyzed_at": datetime.now().isoformat()
        })
        
        # 更新质量门
        if analysis_result.get("success_criteria"):
            state["quality_gates"].update(analysis_result["success_criteria"])
        
        # 记录日志
        state["execution_log"].append({
            "timestamp": datetime.now(),
            "phase": ProjectPhase.REQUIREMENTS,
            "action": "requirements_analyzed",
            "details": analysis_result
        })
        
        logger.info("Requirements analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Error in requirements analysis: {e}")
        state["error_log"].append({
            "timestamp": datetime.now(),
            "phase": ProjectPhase.REQUIREMENTS,
            "error": str(e),
            "severity": "high"
        })
    
    state["updated_at"] = datetime.now()
    return state


async def create_plan(state: ProjectState) -> Dict[str, Any]:
    """
    创建计划节点
    基于需求分析结果，创建详细的执行计划
    """
    logger.info(f"Creating execution plan for project: {state['project_id']}")
    
    # 更新阶段
    state["current_phase"] = ProjectPhase.PLANNING
    state["phase_history"].append({
        "phase": ProjectPhase.PLANNING,
        "started_at": datetime.now(),
        "status": "in_progress"
    })
    
    requirements = state["project_context"].get("requirements_analysis", {})
    suggested_tasks = requirements.get("suggested_tasks", [])
    
    # 创建任务定义
    tasks = []
    task_dependencies = {}
    
    for i, task_info in enumerate(suggested_tasks):
        task_id = f"task_{i+1:03d}"
        
        task = TaskDefinition(
            id=task_id,
            title=task_info["title"],
            description=task_info["description"],
            type=TaskType(task_info.get("type", "custom")),
            priority=task_info.get("priority", 3),
            estimated_time=task_info.get("estimated_time", 60),
            quality_criteria={
                "accuracy": 0.8,
                "completeness": 0.9
            }
        )
        
        tasks.append(task)
        
        # 设置依赖关系（简单的顺序依赖）
        if i > 0:
            task_dependencies[task_id] = [f"task_{i:03d}"]
        else:
            task_dependencies[task_id] = []
        
        # 初始化任务状态
        state["task_status"][task_id] = TaskStatus.PENDING
    
    # 计算关键路径（简化版）
    critical_path = [task.id for task in tasks]
    
    # 创建执行计划
    execution_plan = {
        "total_tasks": len(tasks),
        "estimated_duration": sum(task.estimated_time for task in tasks),
        "parallelizable_tasks": [],  # TODO: 识别可并行的任务
        "milestones": [
            {
                "name": "数据收集完成",
                "tasks": [t.id for t in tasks if t.type == TaskType.DATA_COLLECTION],
                "target_date": None
            },
            {
                "name": "分析完成",
                "tasks": [t.id for t in tasks if t.type == TaskType.DEEP_ANALYSIS],
                "target_date": None
            }
        ]
    }
    
    # 更新状态
    state["tasks"] = tasks
    state["task_dependencies"] = task_dependencies
    state["critical_path"] = critical_path
    state["execution_plan"] = execution_plan
    
    # 记录日志
    state["execution_log"].append({
        "timestamp": datetime.now(),
        "phase": ProjectPhase.PLANNING,
        "action": "plan_created",
        "details": {
            "task_count": len(tasks),
            "estimated_duration": execution_plan["estimated_duration"]
        }
    })
    
    logger.info(f"Execution plan created with {len(tasks)} tasks")
    
    state["updated_at"] = datetime.now()
    return state


async def validate_plan(state: ProjectState) -> Dict[str, Any]:
    """
    验证计划节点
    检查计划的完整性、可行性和质量
    """
    logger.info(f"Validating execution plan for project: {state['project_id']}")
    
    validation_results = {
        "is_valid": True,
        "issues": [],
        "warnings": [],
        "plan_quality": 0.0
    }
    
    # 检查是否有任务
    if not state.get("tasks"):
        validation_results["is_valid"] = False
        validation_results["issues"].append("No tasks found in plan")
    
    # 检查任务依赖
    task_ids = {task.id for task in state.get("tasks", [])}
    for task_id, deps in state.get("task_dependencies", {}).items():
        for dep in deps:
            if dep not in task_ids:
                validation_results["is_valid"] = False
                validation_results["issues"].append(
                    f"Task {task_id} depends on non-existent task {dep}"
                )
    
    # 检查循环依赖
    if _has_circular_dependency(state.get("task_dependencies", {})):
        validation_results["is_valid"] = False
        validation_results["issues"].append("Circular dependency detected")
    
    # 计算计划质量分数
    quality_factors = {
        "has_tasks": 1.0 if state.get("tasks") else 0.0,
        "has_dependencies": 1.0 if state.get("task_dependencies") else 0.5,
        "has_estimates": 1.0 if all(
            task.estimated_time for task in state.get("tasks", [])
        ) else 0.7,
        "reasonable_size": 1.0 if 3 <= len(state.get("tasks", [])) <= 20 else 0.8
    }
    
    validation_results["plan_quality"] = sum(quality_factors.values()) / len(quality_factors)
    
    # 更新状态
    state["metrics"]["plan_quality"] = validation_results["plan_quality"]
    state["metrics"]["plan_valid"] = validation_results["is_valid"]
    
    # 记录日志
    state["execution_log"].append({
        "timestamp": datetime.now(),
        "phase": ProjectPhase.PLANNING,
        "action": "plan_validated",
        "details": validation_results
    })
    
    if not validation_results["is_valid"]:
        state["error_log"].extend([
            {
                "timestamp": datetime.now(),
                "phase": ProjectPhase.PLANNING,
                "error": issue,
                "severity": "high"
            }
            for issue in validation_results["issues"]
        ])
    
    logger.info(f"Plan validation completed: quality={validation_results['plan_quality']}")
    
    state["updated_at"] = datetime.now()
    return state


async def execute_task(state: ProjectState) -> Dict[str, Any]:
    """
    执行任务节点
    执行单个任务，更新进度
    """
    logger.info(f"Executing tasks for project: {state['project_id']}")
    
    # 更新阶段
    if state["current_phase"] != ProjectPhase.EXECUTION:
        state["current_phase"] = ProjectPhase.EXECUTION
        state["phase_history"].append({
            "phase": ProjectPhase.EXECUTION,
            "started_at": datetime.now(),
            "status": "in_progress"
        })
    
    # 查找下一个可执行的任务
    next_task = _find_next_executable_task(state)
    
    if not next_task:
        logger.info("No executable tasks found")
        return state
    
    logger.info(f"Executing task: {next_task.id} - {next_task.title}")
    
    # 更新任务状态
    state["task_status"][next_task.id] = TaskStatus.IN_PROGRESS
    state["active_tasks"] = [next_task.id]
    
    try:
        # 模拟任务执行
        # 实际实现中，这里会调用相应的执行器
        await asyncio.sleep(0.5)  # 模拟执行时间
        
        # 创建任务结果
        task_result = {
            "task_id": next_task.id,
            "status": "completed",
            "output": f"Results for {next_task.title}",
            "metrics": {
                "accuracy": 0.85,
                "completeness": 0.9,
                "execution_time": 45.2
            },
            "artifacts": []
        }
        
        # 更新任务状态
        state["task_status"][next_task.id] = TaskStatus.COMPLETED
        state["completed_tasks"].append(next_task.id)
        state["active_tasks"].remove(next_task.id)
        
        # 保存任务快照
        if next_task.id not in state["task_memories"]:
            state["task_memories"][next_task.id] = []
        
        state["task_memories"][next_task.id].append({
            "task_id": next_task.id,
            "timestamp": datetime.now(),
            "status": TaskStatus.COMPLETED,
            "progress": 1.0,
            "results": task_result
        })
        
        # 记录日志
        state["execution_log"].append({
            "timestamp": datetime.now(),
            "phase": ProjectPhase.EXECUTION,
            "action": "task_completed",
            "task_id": next_task.id,
            "details": task_result
        })
        
        logger.info(f"Task {next_task.id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error executing task {next_task.id}: {e}")
        
        # 更新任务状态为失败
        state["task_status"][next_task.id] = TaskStatus.FAILED
        state["active_tasks"].remove(next_task.id)
        
        # 记录错误
        state["error_log"].append({
            "timestamp": datetime.now(),
            "phase": ProjectPhase.EXECUTION,
            "task_id": next_task.id,
            "error": str(e),
            "severity": "high"
        })
    
    # 更新项目进度
    total_tasks = len(state["tasks"])
    completed_tasks = len(state["completed_tasks"])
    state["metrics"]["progress"] = completed_tasks / total_tasks if total_tasks > 0 else 0
    
    state["updated_at"] = datetime.now()
    return state


async def monitor_progress(state: ProjectState) -> Dict[str, Any]:
    """
    监控进度节点
    检查执行状态，识别问题，调整策略
    """
    logger.info(f"Monitoring progress for project: {state['project_id']}")
    
    # 计算各种指标
    total_tasks = len(state.get("tasks", []))
    completed_tasks = len(state.get("completed_tasks", []))
    failed_tasks = sum(
        1 for status in state.get("task_status", {}).values()
        if status == TaskStatus.FAILED
    )
    blocked_tasks = len(state.get("blocked_tasks", []))
    
    # 更新进度指标
    progress_metrics = {
        "overall_progress": completed_tasks / total_tasks if total_tasks > 0 else 0,
        "success_rate": completed_tasks / (completed_tasks + failed_tasks) 
                       if (completed_tasks + failed_tasks) > 0 else 1.0,
        "blocked_ratio": blocked_tasks / total_tasks if total_tasks > 0 else 0,
        "velocity": _calculate_velocity(state),
        "estimated_completion": _estimate_completion_time(state)
    }
    
    state["metrics"].update(progress_metrics)
    
    # 识别问题
    issues = []
    
    if progress_metrics["success_rate"] < 0.7:
        issues.append({
            "type": "low_success_rate",
            "severity": "high",
            "message": f"Success rate is too low: {progress_metrics['success_rate']:.2%}"
        })
    
    if progress_metrics["blocked_ratio"] > 0.3:
        issues.append({
            "type": "high_blocked_ratio",
            "severity": "medium",
            "message": f"Too many blocked tasks: {blocked_tasks}/{total_tasks}"
        })
    
    # 检查是否需要干预
    if issues:
        state["execution_log"].append({
            "timestamp": datetime.now(),
            "phase": ProjectPhase.EXECUTION,
            "action": "issues_detected",
            "details": issues
        })
    
    # 更新阻塞任务
    _update_blocked_tasks(state)
    
    logger.info(f"Progress monitoring completed: {progress_metrics['overall_progress']:.2%}")
    
    state["updated_at"] = datetime.now()
    return state


async def evaluate_quality(state: ProjectState) -> Dict[str, Any]:
    """
    质量评估节点
    评估已完成任务的质量，确保满足标准
    """
    logger.info(f"Evaluating quality for project: {state['project_id']}")
    
    # 获取最近完成的任务
    recent_tasks = state["completed_tasks"][-3:]  # 评估最近3个任务
    
    quality_scores = {}
    overall_quality = 0.0
    
    for task_id in recent_tasks:
        task_memories = state.get("task_memories", {}).get(task_id, [])
        if not task_memories:
            continue
        
        latest_result = task_memories[-1].get("results", {})
        task_metrics = latest_result.get("metrics", {})
        
        # 计算任务质量分数
        task_quality = {
            "accuracy": task_metrics.get("accuracy", 0.8),
            "completeness": task_metrics.get("completeness", 0.85),
            "timeliness": 1.0 if task_metrics.get("execution_time", 100) < 120 else 0.8
        }
        
        # 加权平均
        task_score = (
            task_quality["accuracy"] * 0.4 +
            task_quality["completeness"] * 0.4 +
            task_quality["timeliness"] * 0.2
        )
        
        quality_scores[task_id] = {
            "score": task_score,
            "details": task_quality
        }
    
    # 计算整体质量
    if quality_scores:
        overall_quality = sum(
            q["score"] for q in quality_scores.values()
        ) / len(quality_scores)
    
    # 更新状态
    state["metrics"]["quality_score"] = overall_quality
    state["metrics"]["task_quality_scores"] = quality_scores
    
    # 检查是否满足质量门
    quality_gate_passed = all(
        overall_quality >= threshold
        for criterion, threshold in state.get("quality_gates", {}).items()
        if criterion in ["accuracy", "completeness"]
    )
    
    # 记录评估结果
    state["execution_log"].append({
        "timestamp": datetime.now(),
        "phase": ProjectPhase.EXECUTION,
        "action": "quality_evaluated",
        "details": {
            "overall_quality": overall_quality,
            "quality_gate_passed": quality_gate_passed,
            "evaluated_tasks": recent_tasks
        }
    })
    
    if not quality_gate_passed:
        state["execution_log"].append({
            "timestamp": datetime.now(),
            "phase": ProjectPhase.EXECUTION,
            "action": "quality_gate_failed",
            "severity": "high"
        })
    
    logger.info(f"Quality evaluation completed: {overall_quality:.2f}")
    
    state["updated_at"] = datetime.now()
    return state


async def record_results(state: ProjectState) -> Dict[str, Any]:
    """
    记录结果节点
    整理和保存执行结果，生成项目洞察
    """
    logger.info(f"Recording results for project: {state['project_id']}")
    
    # 更新阶段
    state["current_phase"] = ProjectPhase.RECORDING
    state["phase_history"].append({
        "phase": ProjectPhase.RECORDING,
        "started_at": datetime.now(),
        "status": "in_progress"
    })
    
    # 收集所有任务结果
    all_results = []
    for task_id in state.get("completed_tasks", []):
        task_memories = state.get("task_memories", {}).get(task_id, [])
        if task_memories:
            latest_result = task_memories[-1].get("results", {})
            all_results.append({
                "task_id": task_id,
                "output": latest_result.get("output", ""),
                "metrics": latest_result.get("metrics", {}),
                "artifacts": latest_result.get("artifacts", [])
            })
    
    # 生成项目洞察
    insights = []
    
    # 洞察1：整体表现
    overall_metrics = state.get("metrics", {})
    insights.append({
        "type": "overall_performance",
        "content": f"项目完成度: {overall_metrics.get('progress', 0):.2%}",
        "metrics": {
            "progress": overall_metrics.get("progress", 0),
            "quality": overall_metrics.get("quality_score", 0),
            "success_rate": overall_metrics.get("success_rate", 0)
        }
    })
    
    # 洞察2：关键发现
    if all_results:
        key_findings = [
            result["output"] for result in all_results[:3]
        ]
        insights.append({
            "type": "key_findings",
            "content": "主要发现和成果",
            "details": key_findings
        })
    
    # 创建可交付成果
    deliverable = {
        "id": f"deliverable_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "type": "interim_results",
        "created_at": datetime.now(),
        "content": {
            "task_results": all_results,
            "insights": insights,
            "metrics": state.get("metrics", {})
        }
    }
    
    state["deliverables"].append(deliverable)
    state["project_insights"].extend(insights)
    
    # 记录日志
    state["execution_log"].append({
        "timestamp": datetime.now(),
        "phase": ProjectPhase.RECORDING,
        "action": "results_recorded",
        "details": {
            "results_count": len(all_results),
            "insights_count": len(insights)
        }
    })
    
    logger.info(f"Results recorded: {len(all_results)} task results, {len(insights)} insights")
    
    state["updated_at"] = datetime.now()
    return state


async def complete_project(state: ProjectState) -> Dict[str, Any]:
    """
    完成项目节点
    生成最终报告，归档项目资料
    """
    logger.info(f"Completing project: {state['project_id']}")
    
    # 更新阶段
    state["current_phase"] = ProjectPhase.COMPLETION
    state["phase_history"].append({
        "phase": ProjectPhase.COMPLETION,
        "started_at": datetime.now(),
        "status": "in_progress"
    })
    
    # 生成最终报告
    final_report = {
        "project_id": state["project_id"],
        "project_name": state["project_name"],
        "completion_date": datetime.now(),
        
        # 执行摘要
        "executive_summary": {
            "objectives": state["project_context"].get("requirements_analysis", {}).get("main_objectives", []),
            "total_tasks": len(state.get("tasks", [])),
            "completed_tasks": len(state.get("completed_tasks", [])),
            "success_rate": state["metrics"].get("success_rate", 0),
            "overall_quality": state["metrics"].get("quality_score", 0)
        },
        
        # 详细结果
        "detailed_results": {
            "deliverables": state.get("deliverables", []),
            "insights": state.get("project_insights", []),
            "metrics": state.get("metrics", {})
        },
        
        # 经验教训
        "lessons_learned": {
            "successes": _identify_successes(state),
            "challenges": _identify_challenges(state),
            "recommendations": _generate_recommendations(state)
        },
        
        # 元数据
        "metadata": {
            "created_at": state["created_at"],
            "completed_at": datetime.now(),
            "total_duration": (datetime.now() - state["created_at"]).total_seconds(),
            "phase_history": state["phase_history"]
        }
    }
    
    state["final_report"] = final_report
    
    # 标记所有未完成的任务
    for task_id, status in state["task_status"].items():
        if status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            state["task_status"][task_id] = TaskStatus.CANCELLED
    
    # 清理活动任务
    state["active_tasks"] = []
    
    # 记录完成日志
    state["execution_log"].append({
        "timestamp": datetime.now(),
        "phase": ProjectPhase.COMPLETION,
        "action": "project_completed",
        "details": {
            "total_duration": final_report["metadata"]["total_duration"],
            "final_success_rate": final_report["executive_summary"]["success_rate"]
        }
    })
    
    logger.info(f"Project completed successfully: {state['project_id']}")
    
    state["updated_at"] = datetime.now()
    return state


# 辅助函数

def _has_circular_dependency(dependencies: Dict[str, List[str]]) -> bool:
    """检查是否存在循环依赖"""
    visited = set()
    rec_stack = set()
    
    def has_cycle(node):
        visited.add(node)
        rec_stack.add(node)
        
        for neighbor in dependencies.get(node, []):
            if neighbor not in visited:
                if has_cycle(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True
        
        rec_stack.remove(node)
        return False
    
    for node in dependencies:
        if node not in visited:
            if has_cycle(node):
                return True
    
    return False


def _find_next_executable_task(state: ProjectState) -> Optional[TaskDefinition]:
    """查找下一个可执行的任务"""
    for task in state.get("tasks", []):
        task_id = task.id
        status = state["task_status"].get(task_id)
        
        # 跳过已完成或失败的任务
        if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.IN_PROGRESS]:
            continue
        
        # 检查依赖是否满足
        dependencies = state["task_dependencies"].get(task_id, [])
        dependencies_satisfied = all(
            state["task_status"].get(dep) == TaskStatus.COMPLETED
            for dep in dependencies
        )
        
        if dependencies_satisfied:
            return task
    
    return None


def _calculate_velocity(state: ProjectState) -> float:
    """计算执行速度（任务/小时）"""
    completed_count = len(state.get("completed_tasks", []))
    
    if completed_count == 0:
        return 0.0
    
    # 获取第一个和最后一个完成的任务时间
    execution_logs = [
        log for log in state.get("execution_log", [])
        if log.get("action") == "task_completed"
    ]
    
    if len(execution_logs) < 2:
        return 1.0  # 默认速度
    
    first_completion = execution_logs[0]["timestamp"]
    last_completion = execution_logs[-1]["timestamp"]
    
    duration_hours = (last_completion - first_completion).total_seconds() / 3600
    
    if duration_hours == 0:
        return completed_count
    
    return completed_count / duration_hours


def _estimate_completion_time(state: ProjectState) -> Optional[datetime]:
    """估计完成时间"""
    remaining_tasks = len(state.get("tasks", [])) - len(state.get("completed_tasks", []))
    
    if remaining_tasks == 0:
        return datetime.now()
    
    velocity = _calculate_velocity(state)
    
    if velocity == 0:
        return None
    
    hours_remaining = remaining_tasks / velocity
    
    return datetime.now() + timedelta(hours=hours_remaining)


def _update_blocked_tasks(state: ProjectState) -> None:
    """更新阻塞的任务"""
    blocked = []
    
    for task in state.get("tasks", []):
        task_id = task.id
        status = state["task_status"].get(task_id)
        
        if status == TaskStatus.PENDING:
            dependencies = state["task_dependencies"].get(task_id, [])
            
            # 检查是否有失败的依赖
            failed_deps = [
                dep for dep in dependencies
                if state["task_status"].get(dep) == TaskStatus.FAILED
            ]
            
            if failed_deps:
                blocked.append(task_id)
                state["task_status"][task_id] = TaskStatus.BLOCKED
    
    state["blocked_tasks"] = blocked


def _identify_successes(state: ProjectState) -> List[str]:
    """识别项目成功点"""
    successes = []
    
    if state["metrics"].get("success_rate", 0) > 0.8:
        successes.append("高任务成功率")
    
    if state["metrics"].get("quality_score", 0) > 0.85:
        successes.append("优秀的整体质量")
    
    if len(state.get("project_insights", [])) > 5:
        successes.append("生成了丰富的项目洞察")
    
    return successes


def _identify_challenges(state: ProjectState) -> List[str]:
    """识别项目挑战"""
    challenges = []
    
    if len(state.get("error_log", [])) > 5:
        challenges.append("执行过程中遇到多个错误")
    
    if state.get("blocked_tasks"):
        challenges.append(f"有{len(state['blocked_tasks'])}个任务被阻塞")
    
    if state["metrics"].get("success_rate", 1) < 0.7:
        challenges.append("任务成功率偏低")
    
    return challenges


def _generate_recommendations(state: ProjectState) -> List[str]:
    """生成改进建议"""
    recommendations = []
    
    # 基于错误日志
    error_types = {}
    for error in state.get("error_log", []):
        error_type = error.get("phase", "unknown")
        error_types[error_type] = error_types.get(error_type, 0) + 1
    
    most_error_phase = max(error_types.items(), key=lambda x: x[1])[0] if error_types else None
    
    if most_error_phase:
        recommendations.append(f"重点改进{most_error_phase}阶段的稳定性")
    
    # 基于执行效率
    if _calculate_velocity(state) < 0.5:
        recommendations.append("提高任务执行效率，考虑并行处理")
    
    # 基于质量
    if state["metrics"].get("quality_score", 1) < 0.8:
        recommendations.append("加强质量控制，增加验证步骤")
    
    return recommendations