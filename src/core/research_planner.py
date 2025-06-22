"""
研究规划服务
实现类似DeepResearch的智能研究工作流，包括研究计划生成、任务分解和执行跟踪
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
from datetime import datetime, timedelta
from langchain.schema import Document
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain.chains import LLMChain

logger = logging.getLogger(__name__)

class ResearchPhase(Enum):
    """研究阶段"""
    PLANNING = "planning"  # 规划阶段
    EXPLORATION = "exploration"  # 探索阶段
    ANALYSIS = "analysis"  # 分析阶段
    SYNTHESIS = "synthesis"  # 综合阶段
    VALIDATION = "validation"  # 验证阶段
    REPORTING = "reporting"  # 报告阶段

class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class TaskType(Enum):
    """任务类型"""
    LITERATURE_REVIEW = "literature_review"
    CONCEPT_EXTRACTION = "concept_extraction"
    RELATIONSHIP_MAPPING = "relationship_mapping"
    GAP_ANALYSIS = "gap_analysis"
    HYPOTHESIS_GENERATION = "hypothesis_generation"
    EVIDENCE_COLLECTION = "evidence_collection"
    SYNTHESIS = "synthesis"
    VALIDATION = "validation"

@dataclass
class ResearchTask:
    """研究任务"""
    task_id: str
    title: str
    description: str
    task_type: TaskType
    phase: ResearchPhase
    priority: int = 1  # 1-5, 5最高
    dependencies: List[str] = field(default_factory=list)  # 依赖的任务ID
    estimated_duration: timedelta = field(default_factory=lambda: timedelta(hours=1))
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    results: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class ResearchPlan:
    """研究计划"""
    plan_id: str
    title: str
    description: str
    research_question: str
    objectives: List[str]
    scope: Dict[str, Any]
    methodology: str
    timeline: Dict[str, datetime]
    tasks: List[ResearchTask] = field(default_factory=list)
    current_phase: ResearchPhase = ResearchPhase.PLANNING
    progress: float = 0.0  # 0-1
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class ResearchContext:
    """研究上下文"""
    domain: str
    keywords: List[str]
    existing_knowledge: List[str]
    constraints: Dict[str, Any]
    preferences: Dict[str, Any]

class ResearchPlanGenerator:
    """研究计划生成器"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        
        # 研究计划生成提示模板
        self.plan_template = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的研究规划专家。基于用户的研究问题和上下文，生成详细的研究计划。

研究计划应该包括：
1. 明确的研究目标和问题
2. 研究范围和边界
3. 研究方法论
4. 分阶段的任务分解
5. 时间线规划
6. 预期成果

请确保计划具有可执行性和科学性。"""),
            ("human", """
研究问题: {research_question}
研究领域: {domain}
关键词: {keywords}
现有知识: {existing_knowledge}
约束条件: {constraints}
偏好设置: {preferences}

请生成详细的研究计划。
""")
        ])
        
        # 任务分解提示模板
        self.task_template = ChatPromptTemplate.from_messages([
            ("system", """你是一个任务分解专家。将研究目标分解为具体的、可执行的任务。

每个任务应该包括：
1. 明确的任务描述
2. 任务类型和阶段
3. 优先级
4. 预估时间
5. 依赖关系
6. 预期输出

任务类型包括：
- literature_review: 文献综述
- concept_extraction: 概念提取
- relationship_mapping: 关系映射
- gap_analysis: 差距分析
- hypothesis_generation: 假设生成
- evidence_collection: 证据收集
- synthesis: 综合分析
- validation: 验证

研究阶段包括：
- planning: 规划阶段
- exploration: 探索阶段
- analysis: 分析阶段
- synthesis: 综合阶段
- validation: 验证阶段
- reporting: 报告阶段"""),
            ("human", """
研究计划: {research_plan}
当前阶段: {current_phase}

请为当前阶段生成具体的任务列表。
""")
        ])
    
    async def generate_research_plan(
        self,
        research_question: str,
        context: ResearchContext
    ) -> ResearchPlan:
        """生成研究计划"""
        try:
            logger.info(f"生成研究计划: {research_question[:50]}...")
            
            # 1. 生成基础计划
            plan_chain = LLMChain(llm=self.llm, prompt=self.plan_template)
            plan_response = await plan_chain.arun(
                research_question=research_question,
                domain=context.domain,
                keywords=", ".join(context.keywords),
                existing_knowledge=", ".join(context.existing_knowledge),
                constraints=json.dumps(context.constraints, ensure_ascii=False),
                preferences=json.dumps(context.preferences, ensure_ascii=False)
            )
            
            # 2. 解析计划内容
            plan_data = self._parse_plan_response(plan_response)
            
            # 3. 创建研究计划对象
            plan = ResearchPlan(
                plan_id=str(uuid.uuid4()),
                title=plan_data.get("title", f"研究计划: {research_question}"),
                description=plan_data.get("description", ""),
                research_question=research_question,
                objectives=plan_data.get("objectives", []),
                scope=plan_data.get("scope", {}),
                methodology=plan_data.get("methodology", ""),
                timeline=plan_data.get("timeline", {}),
                metadata={
                    "context": context.__dict__,
                    "generated_by": "ResearchPlanGenerator"
                }
            )
            
            # 4. 生成初始任务
            initial_tasks = await self._generate_initial_tasks(plan)
            plan.tasks = initial_tasks
            
            logger.info(f"研究计划生成完成: {plan.plan_id}")
            return plan
            
        except Exception as e:
            logger.error(f"生成研究计划失败: {e}")
            raise
    
    def _parse_plan_response(self, response: str) -> Dict[str, Any]:
        """解析计划响应"""
        # TODO: 实现更智能的响应解析
        # 目前返回基础结构
        return {
            "title": "AI生成的研究计划",
            "description": response,
            "objectives": ["目标1", "目标2", "目标3"],
            "scope": {"领域": "AI研究", "时间范围": "6个月"},
            "methodology": "文献综述 + 实验验证",
            "timeline": {}
        }
    
    async def _generate_initial_tasks(self, plan: ResearchPlan) -> List[ResearchTask]:
        """生成初始任务列表"""
        try:
            # 为规划阶段生成任务
            task_chain = LLMChain(llm=self.llm, prompt=self.task_template)
            task_response = await task_chain.arun(
                research_plan=plan.description,
                current_phase=ResearchPhase.PLANNING.value
            )
            
            # 解析任务
            tasks = self._parse_task_response(task_response, plan.plan_id)
            
            return tasks
            
        except Exception as e:
            logger.error(f"生成初始任务失败: {e}")
            return []
    
    def _parse_task_response(self, response: str, plan_id: str) -> List[ResearchTask]:
        """解析任务响应"""
        # TODO: 实现更智能的任务解析
        # 目前返回基础任务
        base_tasks = [
            {
                "title": "文献调研",
                "description": "收集和分析相关文献",
                "task_type": TaskType.LITERATURE_REVIEW,
                "phase": ResearchPhase.EXPLORATION,
                "priority": 5
            },
            {
                "title": "概念提取",
                "description": "从文献中提取关键概念",
                "task_type": TaskType.CONCEPT_EXTRACTION,
                "phase": ResearchPhase.ANALYSIS,
                "priority": 4,
                "dependencies": ["literature_review"]
            },
            {
                "title": "关系映射",
                "description": "构建概念间的关系图",
                "task_type": TaskType.RELATIONSHIP_MAPPING,
                "phase": ResearchPhase.ANALYSIS,
                "priority": 3,
                "dependencies": ["concept_extraction"]
            }
        ]
        
        tasks = []
        for i, task_data in enumerate(base_tasks):
            task = ResearchTask(
                task_id=f"{plan_id}_task_{i}",
                title=task_data["title"],
                description=task_data["description"],
                task_type=task_data["task_type"],
                phase=task_data["phase"],
                priority=task_data["priority"],
                dependencies=task_data.get("dependencies", []),
                metadata={"plan_id": plan_id}
            )
            tasks.append(task)
        
        return tasks

class TaskExecutor:
    """任务执行器"""
    
    def __init__(self, knowledge_service, llm: ChatOpenAI):
        self.knowledge_service = knowledge_service
        self.llm = llm
        
        # 任务执行器映射
        self.executors = {
            TaskType.LITERATURE_REVIEW: self._execute_literature_review,
            TaskType.CONCEPT_EXTRACTION: self._execute_concept_extraction,
            TaskType.RELATIONSHIP_MAPPING: self._execute_relationship_mapping,
            TaskType.GAP_ANALYSIS: self._execute_gap_analysis,
            TaskType.HYPOTHESIS_GENERATION: self._execute_hypothesis_generation,
            TaskType.EVIDENCE_COLLECTION: self._execute_evidence_collection,
            TaskType.SYNTHESIS: self._execute_synthesis,
            TaskType.VALIDATION: self._execute_validation
        }
    
    async def execute_task(self, task: ResearchTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行研究任务"""
        try:
            logger.info(f"开始执行任务: {task.title}")
            
            # 更新任务状态
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now()
            
            # 获取执行器
            executor = self.executors.get(task.task_type)
            if not executor:
                raise ValueError(f"不支持的任务类型: {task.task_type}")
            
            # 执行任务
            results = await executor(task, context)
            
            # 更新任务状态
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.results = results
            
            logger.info(f"任务执行完成: {task.title}")
            return results
            
        except Exception as e:
            logger.error(f"任务执行失败: {task.title}, 错误: {e}")
            task.status = TaskStatus.FAILED
            task.results = {"error": str(e)}
            raise
    
    async def _execute_literature_review(self, task: ResearchTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行文献综述任务"""
        research_question = context.get("research_question", "")
        keywords = context.get("keywords", [])
        
        # 1. 搜索相关文档
        search_results = await self.knowledge_service.search(
            query=research_question,
            k=20,
            search_type="hybrid"
        )
        
        # 2. 分析文献
        literature_analysis = {
            "total_documents": len(search_results["results"]),
            "key_themes": [],
            "important_findings": [],
            "research_gaps": [],
            "methodology_insights": []
        }
        
        # TODO: 实现更深入的文献分析
        
        return {
            "search_results": search_results,
            "analysis": literature_analysis,
            "recommendations": ["建议1", "建议2", "建议3"]
        }
    
    async def _execute_concept_extraction(self, task: ResearchTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行概念提取任务"""
        # 从前置任务获取文献
        literature_results = context.get("literature_review_results", {})
        
        # TODO: 实现概念提取算法
        concepts = {
            "key_concepts": ["概念1", "概念2", "概念3"],
            "definitions": {},
            "frequency": {},
            "relationships": []
        }
        
        return concepts
    
    async def _execute_relationship_mapping(self, task: ResearchTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行关系映射任务"""
        concepts = context.get("concept_extraction_results", {})
        
        # TODO: 实现关系映射算法
        relationships = {
            "concept_graph": {},
            "relationship_types": ["相关", "包含", "对立"],
            "strength_scores": {}
        }
        
        return relationships
    
    async def _execute_gap_analysis(self, task: ResearchTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行差距分析任务"""
        # TODO: 实现差距分析
        gaps = {
            "knowledge_gaps": ["差距1", "差距2"],
            "methodology_gaps": ["方法差距1"],
            "research_opportunities": ["机会1", "机会2"]
        }
        
        return gaps
    
    async def _execute_hypothesis_generation(self, task: ResearchTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行假设生成任务"""
        # TODO: 实现假设生成
        hypotheses = {
            "hypotheses": ["假设1", "假设2"],
            "testability": {},
            "priority": {}
        }
        
        return hypotheses
    
    async def _execute_evidence_collection(self, task: ResearchTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行证据收集任务"""
        # TODO: 实现证据收集
        evidence = {
            "supporting_evidence": [],
            "contradicting_evidence": [],
            "quality_scores": {}
        }
        
        return evidence
    
    async def _execute_synthesis(self, task: ResearchTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行综合分析任务"""
        # TODO: 实现综合分析
        synthesis = {
            "key_findings": [],
            "conclusions": [],
            "implications": []
        }
        
        return synthesis
    
    async def _execute_validation(self, task: ResearchTask, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行验证任务"""
        # TODO: 实现验证
        validation = {
            "validation_results": {},
            "confidence_scores": {},
            "limitations": []
        }
        
        return validation

class ResearchPlannerService:
    """研究规划服务"""
    
    def __init__(self, knowledge_service, llm: ChatOpenAI):
        self.knowledge_service = knowledge_service
        self.llm = llm
        self.plan_generator = ResearchPlanGenerator(llm)
        self.task_executor = TaskExecutor(knowledge_service, llm)
        
        # 活跃的研究计划
        self.active_plans: Dict[str, ResearchPlan] = {}
        
        # 执行历史
        self.execution_history: List[Dict[str, Any]] = []
    
    async def create_research_plan(
        self,
        research_question: str,
        context: ResearchContext
    ) -> ResearchPlan:
        """创建研究计划"""
        try:
            plan = await self.plan_generator.generate_research_plan(research_question, context)
            self.active_plans[plan.plan_id] = plan
            
            logger.info(f"创建研究计划: {plan.plan_id}")
            return plan
            
        except Exception as e:
            logger.error(f"创建研究计划失败: {e}")
            raise
    
    async def execute_plan(self, plan_id: str) -> Dict[str, Any]:
        """执行研究计划"""
        try:
            plan = self.active_plans.get(plan_id)
            if not plan:
                raise ValueError(f"研究计划不存在: {plan_id}")
            
            logger.info(f"开始执行研究计划: {plan_id}")
            
            execution_context = {
                "research_question": plan.research_question,
                "keywords": plan.metadata.get("context", {}).get("keywords", []),
                "plan_id": plan_id
            }
            
            # 按阶段执行任务
            for phase in ResearchPhase:
                phase_tasks = [task for task in plan.tasks if task.phase == phase]
                if not phase_tasks:
                    continue
                
                logger.info(f"执行阶段: {phase.value}")
                plan.current_phase = phase
                
                # 执行阶段任务
                phase_results = await self._execute_phase_tasks(phase_tasks, execution_context)
                
                # 更新执行上下文
                execution_context.update(phase_results)
                
                # 更新进度
                completed_tasks = len([t for t in plan.tasks if t.status == TaskStatus.COMPLETED])
                plan.progress = completed_tasks / len(plan.tasks) if plan.tasks else 0
                plan.updated_at = datetime.now()
            
            # 记录执行历史
            self.execution_history.append({
                "plan_id": plan_id,
                "execution_time": datetime.now(),
                "results": execution_context,
                "final_progress": plan.progress
            })
            
            logger.info(f"研究计划执行完成: {plan_id}")
            return execution_context
            
        except Exception as e:
            logger.error(f"执行研究计划失败: {plan_id}, 错误: {e}")
            raise
    
    async def _execute_phase_tasks(
        self,
        tasks: List[ResearchTask],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行阶段任务"""
        phase_results = {}
        
        # 按优先级和依赖关系排序
        sorted_tasks = self._sort_tasks_by_dependencies(tasks)
        
        for task in sorted_tasks:
            try:
                # 检查依赖是否完成
                if not self._check_dependencies(task, context):
                    logger.warning(f"任务依赖未满足，跳过: {task.title}")
                    task.status = TaskStatus.SKIPPED
                    continue
                
                # 执行任务
                task_results = await self.task_executor.execute_task(task, context)
                
                # 保存结果
                result_key = f"{task.task_type.value}_results"
                phase_results[result_key] = task_results
                
            except Exception as e:
                logger.error(f"任务执行失败: {task.title}, 错误: {e}")
                continue
        
        return phase_results
    
    def _sort_tasks_by_dependencies(self, tasks: List[ResearchTask]) -> List[ResearchTask]:
        """按依赖关系排序任务"""
        # TODO: 实现拓扑排序
        # 目前按优先级排序
        return sorted(tasks, key=lambda x: x.priority, reverse=True)
    
    def _check_dependencies(self, task: ResearchTask, context: Dict[str, Any]) -> bool:
        """检查任务依赖"""
        for dep in task.dependencies:
            if f"{dep}_results" not in context:
                return False
        return True
    
    def get_plan_status(self, plan_id: str) -> Dict[str, Any]:
        """获取计划状态"""
        plan = self.active_plans.get(plan_id)
        if not plan:
            return {}
        
        task_stats = {
            "total": len(plan.tasks),
            "completed": len([t for t in plan.tasks if t.status == TaskStatus.COMPLETED]),
            "in_progress": len([t for t in plan.tasks if t.status == TaskStatus.IN_PROGRESS]),
            "pending": len([t for t in plan.tasks if t.status == TaskStatus.PENDING]),
            "failed": len([t for t in plan.tasks if t.status == TaskStatus.FAILED])
        }
        
        return {
            "plan_id": plan_id,
            "title": plan.title,
            "current_phase": plan.current_phase.value,
            "progress": plan.progress,
            "task_statistics": task_stats,
            "created_at": plan.created_at.isoformat(),
            "updated_at": plan.updated_at.isoformat()
        }
    
    def list_active_plans(self) -> List[Dict[str, Any]]:
        """列出活跃的研究计划"""
        return [self.get_plan_status(plan_id) for plan_id in self.active_plans.keys()]

def create_research_planner_service(
    knowledge_service,
    llm_config: Optional[Dict[str, Any]] = None
) -> ResearchPlannerService:
    """创建研究规划服务"""
    llm = ChatOpenAI(**(llm_config or {}))
    return ResearchPlannerService(knowledge_service, llm) 