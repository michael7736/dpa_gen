"""
LangGraph编排引擎
实现复杂的分析工作流编排
"""

from typing import Dict, Any, List, Optional, Callable, Union, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import json
from collections import defaultdict

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ..agents import (
    SkimmerAgent, ProgressiveSummaryAgent, KnowledgeGraphAgent,
    OutlineAgent, DeepAnalyzer, PlannerAgent
)
from ..storage import ArtifactStore, MetadataManager
from ...utils.logger import get_logger

logger = get_logger(__name__)


class ExecutionMode(Enum):
    """执行模式"""
    SEQUENTIAL = "sequential"    # 顺序执行
    PARALLEL = "parallel"        # 并行执行
    CONDITIONAL = "conditional"  # 条件执行
    ITERATIVE = "iterative"      # 迭代执行


@dataclass
class WorkflowState:
    """工作流状态"""
    document_id: str
    document_content: str
    current_step: str = "start"
    completed_steps: List[str] = field(default_factory=list)
    artifacts: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_path: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "document_id": self.document_id,
            "current_step": self.current_step,
            "completed_steps": self.completed_steps,
            "artifacts": self.artifacts,
            "errors": self.errors,
            "metadata": self.metadata,
            "execution_path": self.execution_path
        }


@dataclass
class WorkflowNode:
    """工作流节点"""
    name: str
    agent_type: str
    agent_config: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 3
    timeout: Optional[int] = None
    dependencies: List[str] = field(default_factory=list)
    
    
@dataclass
class WorkflowEdge:
    """工作流边"""
    source: str
    target: str
    condition: Optional[Callable[[WorkflowState], bool]] = None
    
    
class OrchestrationEngine:
    """LangGraph编排引擎"""
    
    def __init__(self):
        self.agents = self._initialize_agents()
        self.artifact_store = ArtifactStore()
        self.metadata_manager = MetadataManager()
        self.checkpointer = MemorySaver()
        self.workflows = {}
        logger.info("初始化LangGraph编排引擎")
    
    def _initialize_agents(self) -> Dict[str, Any]:
        """初始化所有可用的Agent"""
        return {
            "skimmer": SkimmerAgent(),
            "summarizer": ProgressiveSummaryAgent(),
            "knowledge_graph": KnowledgeGraphAgent(),
            "outline": OutlineAgent(),
            "deep_analyzer": DeepAnalyzer(),
            "planner": PlannerAgent()
        }
    
    def create_workflow(self, workflow_id: str, name: str, description: str) -> str:
        """
        创建新的工作流
        
        Args:
            workflow_id: 工作流ID
            name: 工作流名称
            description: 工作流描述
            
        Returns:
            工作流ID
        """
        if workflow_id in self.workflows:
            raise ValueError(f"工作流 {workflow_id} 已存在")
        
        self.workflows[workflow_id] = {
            "id": workflow_id,
            "name": name,
            "description": description,
            "nodes": {},
            "edges": [],
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"创建工作流: {workflow_id}")
        return workflow_id
    
    def add_node(
        self, 
        workflow_id: str, 
        node: WorkflowNode
    ) -> None:
        """添加节点到工作流"""
        if workflow_id not in self.workflows:
            raise ValueError(f"工作流 {workflow_id} 不存在")
        
        self.workflows[workflow_id]["nodes"][node.name] = node
        logger.info(f"添加节点 {node.name} 到工作流 {workflow_id}")
    
    def add_edge(
        self, 
        workflow_id: str, 
        edge: WorkflowEdge
    ) -> None:
        """添加边到工作流"""
        if workflow_id not in self.workflows:
            raise ValueError(f"工作流 {workflow_id} 不存在")
        
        self.workflows[workflow_id]["edges"].append(edge)
        logger.info(f"添加边 {edge.source} -> {edge.target} 到工作流 {workflow_id}")
    
    async def execute_workflow(
        self,
        workflow_id: str,
        document_id: str,
        document_content: str,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行工作流
        
        Args:
            workflow_id: 工作流ID
            document_id: 文档ID
            document_content: 文档内容
            initial_state: 初始状态
            
        Returns:
            执行结果
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"工作流 {workflow_id} 不存在")
        
        workflow = self.workflows[workflow_id]
        
        # 初始化状态
        state = WorkflowState(
            document_id=document_id,
            document_content=document_content,
            metadata=initial_state or {}
        )
        
        # 构建LangGraph
        graph = self._build_graph(workflow, state)
        
        # 执行工作流
        start_time = datetime.now()
        
        try:
            # 编译图
            app = graph.compile(checkpointer=self.checkpointer)
            
            # 执行
            final_state = await app.ainvoke(
                state.to_dict(),
                {"configurable": {"thread_id": f"{workflow_id}_{document_id}"}}
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # 保存执行记录
            await self._save_execution_record(
                workflow_id=workflow_id,
                document_id=document_id,
                state=final_state,
                duration=duration
            )
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "document_id": document_id,
                "final_state": final_state,
                "execution_path": final_state.get("execution_path", []),
                "artifacts": final_state.get("artifacts", {}),
                "metadata": {
                    "duration": duration,
                    "completed_steps": len(final_state.get("completed_steps", [])),
                    "errors": len(final_state.get("errors", []))
                }
            }
            
        except Exception as e:
            logger.error(f"工作流执行失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "workflow_id": workflow_id,
                "document_id": document_id,
                "error": str(e),
                "metadata": {
                    "duration": (datetime.now() - start_time).total_seconds()
                }
            }
    
    def _build_graph(
        self, 
        workflow: Dict[str, Any], 
        initial_state: WorkflowState
    ) -> StateGraph:
        """构建LangGraph"""
        # 创建状态图
        graph = StateGraph(dict)
        
        # 添加节点
        for node_name, node in workflow["nodes"].items():
            graph.add_node(
                node_name,
                self._create_node_function(node)
            )
        
        # 添加边
        for edge in workflow["edges"]:
            if edge.condition:
                # 条件边
                graph.add_conditional_edges(
                    edge.source,
                    edge.condition,
                    {True: edge.target, False: END}
                )
            else:
                # 普通边
                graph.add_edge(edge.source, edge.target)
        
        # 设置入口点
        entry_nodes = self._find_entry_nodes(workflow)
        if entry_nodes:
            graph.set_entry_point(entry_nodes[0])
        
        return graph
    
    def _create_node_function(self, node: WorkflowNode) -> Callable:
        """创建节点执行函数"""
        async def node_function(state: Dict[str, Any]) -> Dict[str, Any]:
            logger.info(f"执行节点: {node.name}")
            
            # 更新当前步骤
            state["current_step"] = node.name
            state["execution_path"].append(node.name)
            
            try:
                # 检查依赖
                if node.dependencies:
                    missing = [d for d in node.dependencies 
                             if d not in state["completed_steps"]]
                    if missing:
                        raise ValueError(f"缺少依赖: {missing}")
                
                # 获取对应的Agent
                agent = self.agents.get(node.agent_type)
                if not agent:
                    raise ValueError(f"未知的Agent类型: {node.agent_type}")
                
                # 准备输入
                input_data = {
                    "document_id": state["document_id"],
                    "document_content": state["document_content"],
                    **node.agent_config
                }
                
                # 添加依赖的artifacts
                for dep in node.dependencies:
                    if dep in state["artifacts"]:
                        input_data[f"{dep}_result"] = state["artifacts"][dep]
                
                # 执行Agent
                result = await agent.process(input_data)
                
                if result["success"]:
                    # 保存结果
                    state["artifacts"][node.name] = result["result"]
                    state["completed_steps"].append(node.name)
                    
                    # 保存到物料库
                    await self.artifact_store.save_artifact(
                        document_id=state["document_id"],
                        analysis_type=node.agent_type,
                        content=result["result"],
                        execution_time_seconds=int(result["metadata"]["duration"]),
                        token_usage=result["metadata"].get("tokens_used", 0),
                        model_used=agent.model_name if hasattr(agent, "model_name") else "unknown",
                        created_by="orchestrator"
                    )
                else:
                    # 记录错误
                    state["errors"].append({
                        "node": node.name,
                        "error": result.get("error", "未知错误"),
                        "timestamp": datetime.now().isoformat()
                    })
                
            except Exception as e:
                logger.error(f"节点 {node.name} 执行失败: {str(e)}")
                state["errors"].append({
                    "node": node.name,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                
                # 重试逻辑
                if hasattr(state, "_retry_count"):
                    state["_retry_count"][node.name] = state["_retry_count"].get(node.name, 0) + 1
                    if state["_retry_count"][node.name] < node.retry_count:
                        logger.info(f"重试节点 {node.name} ({state['_retry_count'][node.name]}/{node.retry_count})")
                        return await node_function(state)
                else:
                    state["_retry_count"] = {node.name: 1}
            
            return state
        
        return node_function
    
    def _find_entry_nodes(self, workflow: Dict[str, Any]) -> List[str]:
        """找出入口节点（没有入边的节点）"""
        all_nodes = set(workflow["nodes"].keys())
        target_nodes = {edge.target for edge in workflow["edges"]}
        return list(all_nodes - target_nodes)
    
    async def _save_execution_record(
        self,
        workflow_id: str,
        document_id: str,
        state: Dict[str, Any],
        duration: float
    ) -> None:
        """保存执行记录"""
        record = {
            "workflow_id": workflow_id,
            "document_id": document_id,
            "execution_path": state.get("execution_path", []),
            "completed_steps": state.get("completed_steps", []),
            "errors": state.get("errors", []),
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
        
        # 保存到元数据
        await self.metadata_manager.update_metadata(
            document_id=document_id,
            updates={
                "last_workflow_execution": record,
                "workflow_history": [record]  # 可以追加历史记录
            }
        )
    
    # 预定义的工作流模板
    def create_standard_analysis_workflow(self) -> str:
        """创建标准分析工作流"""
        workflow_id = "standard_analysis"
        
        self.create_workflow(
            workflow_id=workflow_id,
            name="标准文档分析",
            description="包含略读、摘要、知识图谱的标准分析流程"
        )
        
        # 添加节点
        self.add_node(workflow_id, WorkflowNode(
            name="skim",
            agent_type="skimmer"
        ))
        
        self.add_node(workflow_id, WorkflowNode(
            name="summary",
            agent_type="summarizer",
            agent_config={"summary_level": "level_3"},
            dependencies=["skim"]
        ))
        
        self.add_node(workflow_id, WorkflowNode(
            name="knowledge_graph",
            agent_type="knowledge_graph",
            agent_config={"extraction_mode": "comprehensive"},
            dependencies=["skim"]
        ))
        
        self.add_node(workflow_id, WorkflowNode(
            name="outline",
            agent_type="outline",
            agent_config={"dimension": "all"},
            dependencies=["summary"]
        ))
        
        # 添加边
        self.add_edge(workflow_id, WorkflowEdge("skim", "summary"))
        self.add_edge(workflow_id, WorkflowEdge("skim", "knowledge_graph"))
        self.add_edge(workflow_id, WorkflowEdge("summary", "outline"))
        
        return workflow_id
    
    def create_critical_review_workflow(self) -> str:
        """创建批判性审查工作流"""
        workflow_id = "critical_review"
        
        self.create_workflow(
            workflow_id=workflow_id,
            name="批判性审查",
            description="深度分析文档的论证质量和逻辑严密性"
        )
        
        # 添加节点
        self.add_node(workflow_id, WorkflowNode(
            name="skim",
            agent_type="skimmer"
        ))
        
        self.add_node(workflow_id, WorkflowNode(
            name="deep_analysis",
            agent_type="deep_analyzer",
            agent_config={
                "analysis_types": ["evidence_chain", "critical_thinking", "cross_reference"]
            },
            dependencies=["skim"]
        ))
        
        # 添加边
        self.add_edge(workflow_id, WorkflowEdge("skim", "deep_analysis"))
        
        return workflow_id
    
    def create_adaptive_workflow(self) -> str:
        """创建自适应工作流（根据文档质量动态调整）"""
        workflow_id = "adaptive_analysis"
        
        self.create_workflow(
            workflow_id=workflow_id,
            name="自适应分析",
            description="根据文档质量动态调整分析深度"
        )
        
        # 添加节点
        self.add_node(workflow_id, WorkflowNode(
            name="skim",
            agent_type="skimmer"
        ))
        
        self.add_node(workflow_id, WorkflowNode(
            name="quick_summary",
            agent_type="summarizer",
            agent_config={"summary_level": "level_2"}
        ))
        
        self.add_node(workflow_id, WorkflowNode(
            name="deep_summary",
            agent_type="summarizer",
            agent_config={"summary_level": "level_5"}
        ))
        
        self.add_node(workflow_id, WorkflowNode(
            name="quick_kg",
            agent_type="knowledge_graph",
            agent_config={"extraction_mode": "quick"}
        ))
        
        self.add_node(workflow_id, WorkflowNode(
            name="comprehensive_kg",
            agent_type="knowledge_graph",
            agent_config={"extraction_mode": "comprehensive"}
        ))
        
        # 条件函数
        def is_high_quality(state: Dict[str, Any]) -> bool:
            skim_result = state.get("artifacts", {}).get("skim", {})
            quality = skim_result.get("quality_assessment", {}).get("level", "中")
            return quality == "高"
        
        # 添加条件边
        self.add_edge(workflow_id, WorkflowEdge(
            source="skim",
            target="deep_summary",
            condition=is_high_quality
        ))
        
        self.add_edge(workflow_id, WorkflowEdge(
            source="skim",
            target="quick_summary",
            condition=lambda s: not is_high_quality(s)
        ))
        
        self.add_edge(workflow_id, WorkflowEdge(
            source="skim",
            target="comprehensive_kg",
            condition=is_high_quality
        ))
        
        self.add_edge(workflow_id, WorkflowEdge(
            source="skim",
            target="quick_kg",
            condition=lambda s: not is_high_quality(s)
        ))
        
        return workflow_id