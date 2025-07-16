"""
DPA认知工作流 - 基于LangGraph的完整认知循环实现
"""

from typing import Dict, Any, List, Optional, Literal
from datetime import datetime
import asyncio

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ..state import DPACognitiveState, StateManager
from ..storage import create_cognitive_storage
from ..memory.memory_bank import create_memory_bank_manager
from ...utils.logger import get_logger

logger = get_logger(__name__)


class CognitiveWorkflow:
    """认知工作流管理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.storage = create_cognitive_storage()
        self.memory_bank = create_memory_bank_manager()
        self.state_manager = StateManager()
        self.mock_mode = self.config.get("mock_mode", False)
        
        # 初始化LLM
        if not self.mock_mode:
            try:
                from ...config.settings import get_settings
                settings = get_settings()
                if settings.ai_model.openai_api_key:
                    self.llm = ChatOpenAI(
                        model=settings.ai_model.default_llm_model,
                        temperature=settings.ai_model.llm_temperature,
                        openai_api_key=settings.ai_model.openai_api_key,
                        openai_api_base=settings.ai_model.openai_base_url
                    )
                    logger.info("Cognitive Workflow LLM initialized successfully")
                else:
                    logger.warning("OpenAI API key not found, using mock mode")
                    self.mock_mode = True
            except Exception as e:
                logger.warning(f"Failed to initialize LLM: {e}, using mock mode")
                self.mock_mode = True
        
        # 构建工作流
        self.app = self._build_workflow()
        
    def _build_workflow(self) -> StateGraph:
        """构建完整的认知工作流"""
        workflow = StateGraph(DPACognitiveState)
        
        # === 核心节点定义 ===
        
        # 感知与注意力节点
        workflow.add_node("perceive", self.perceive_input)
        workflow.add_node("attend", self.focus_attention)
        
        # 记忆管理节点
        workflow.add_node("encode_memory", self.encode_to_memory)
        workflow.add_node("consolidate_memory", self.consolidate_memories)
        workflow.add_node("retrieve_memory", self.retrieve_from_memory)
        
        # 文档处理节点
        workflow.add_node("process_document", self.process_document)
        workflow.add_node("extract_knowledge", self.extract_to_graph)
        
        # 推理与理解节点
        workflow.add_node("reason", self.reasoning_engine)
        workflow.add_node("understand", self.semantic_understanding)
        
        # 学习规划节点
        workflow.add_node("identify_gaps", self.identify_knowledge_gaps)
        workflow.add_node("generate_hypotheses", self.generate_hypotheses)
        workflow.add_node("plan_learning", self.create_learning_plan)
        
        # 行动执行节点
        workflow.add_node("execute_action", self.execute_planned_action)
        workflow.add_node("verify_hypothesis", self.verify_hypothesis)
        
        # 元认知节点
        workflow.add_node("self_evaluate", self.evaluate_performance)
        workflow.add_node("reflect", self.reflect_on_progress)
        workflow.add_node("adapt", self.adapt_strategy)
        
        # 记忆库节点
        workflow.add_node("sync_memory_bank", self.sync_with_memory_bank)
        workflow.add_node("update_summary", self.update_dynamic_summary)
        
        # === 条件路由 ===
        
        # 入口路由
        workflow.add_conditional_edges(
            "perceive",
            self.route_by_input_type,
            {
                "document": "process_document",
                "query": "attend",
                "hypothesis": "verify_hypothesis",
                "reflect": "self_evaluate"
            }
        )
        
        # 注意力路由
        workflow.add_conditional_edges(
            "attend",
            self.check_working_memory,
            {
                "overflow": "consolidate_memory",
                "normal": "retrieve_memory"
            }
        )
        
        # 文档处理路由
        workflow.add_edge("process_document", "extract_knowledge")
        workflow.add_edge("extract_knowledge", "encode_memory")
        
        # 记忆路由
        workflow.add_edge("encode_memory", "identify_gaps")
        workflow.add_edge("retrieve_memory", "reason")
        
        # 推理路由
        workflow.add_conditional_edges(
            "reason",
            self.check_understanding,
            {
                "understood": "execute_action",
                "unclear": "understand",
                "need_more": "retrieve_memory"
            }
        )
        
        # 学习路由
        workflow.add_conditional_edges(
            "identify_gaps",
            self.evaluate_gap_severity,
            {
                "critical": "plan_learning",
                "minor": "generate_hypotheses",
                "none": "self_evaluate"
            }
        )
        
        # 执行路由
        workflow.add_edge("execute_action", "sync_memory_bank")
        workflow.add_edge("sync_memory_bank", "reflect")
        
        # 反思循环
        workflow.add_conditional_edges(
            "reflect",
            self.should_continue,
            {
                "continue": "perceive",
                "adapt": "adapt",
                "complete": END
            }
        )
        
        # 适应后继续
        workflow.add_edge("adapt", "perceive")
        
        # 设置入口
        workflow.set_entry_point("perceive")
        
        # 编译工作流
        # 暂时使用内存检查点，后续可以切换到PostgreSQL
        checkpointer = MemorySaver()
        
        return workflow.compile(
            checkpointer=checkpointer,
            interrupt_before=["execute_action", "adapt"]  # 人机协作点
        )
    
    # === 节点实现 ===
    
    async def perceive_input(self, state: DPACognitiveState) -> DPACognitiveState:
        """感知输入 - 理解用户意图和内容类型"""
        logger.info("Perceiving input...")
        
        # 清理过期的感觉缓冲
        state = self.state_manager.clear_sensory_buffer(state)
        
        if not state["messages"]:
            state["error_log"].append({
                "timestamp": datetime.now(),
                "error": "No input messages"
            })
            return state
        
        last_message = state["messages"][-1]
        
        # 将输入存入感觉缓冲
        state["sensory_buffer"]["current_input"] = {
            "content": last_message.content,
            "timestamp": datetime.now(),
            "type": "user_message"
        }
        
        # 分析输入类型和意图
        analysis_prompt = f"""
        分析以下输入，确定：
        1. 输入类型（document/query/hypothesis/reflect）
        2. 主要意图
        3. 关键实体
        4. 所需的认知资源
        
        输入：{last_message.content[:500]}
        
        返回JSON格式。
        """
        
        if self.mock_mode:
            # 模拟分析结果
            response_content = '{"type": "query", "intent": "research", "entities": ["认知架构", "人工智能"], "resources": ["general"]}'
        else:
            response = await self.llm.ainvoke([
                SystemMessage(content="你是一个认知分析专家。"),
                HumanMessage(content=analysis_prompt)
            ])
            response_content = response.content
        
        # 解析分析结果
        try:
            import json
            analysis = json.loads(response_content)
        except:
            analysis = {
                "type": "query",
                "intent": "unknown",
                "entities": [],
                "resources": ["general"]
            }
        
        # 更新状态
        state["sensory_buffer"]["analysis"] = analysis
        state["processing_status"] = "perceiving"
        
        # 记录执行历史
        state = self.state_manager.add_to_execution_history(state, "perceive_input")
        
        return state
    
    async def focus_attention(self, state: DPACognitiveState) -> DPACognitiveState:
        """聚焦注意力 - 确定处理优先级"""
        logger.info("Focusing attention...")
        
        analysis = state["sensory_buffer"].get("analysis", {})
        
        # 根据意图调整注意力权重
        if analysis.get("intent") == "research":
            # 研究模式 - 关注深度理解
            state = self.state_manager.update_attention(state, "depth_processing", 0.3)
            state = self.state_manager.update_attention(state, "hypothesis_generation", 0.2)
        elif analysis.get("intent") == "query":
            # 查询模式 - 关注快速检索
            state = self.state_manager.update_attention(state, "retrieval_speed", 0.3)
            state = self.state_manager.update_attention(state, "relevance_filtering", 0.2)
        
        # 识别关键实体并加入工作记忆
        for entity in analysis.get("entities", [])[:3]:  # 限制数量
            state["working_memory"][f"entity_{entity}"] = {
                "value": entity,
                "type": "entity",
                "timestamp": datetime.now()
            }
            state = self.state_manager.update_attention(state, f"entity_{entity}", 0.6)
        
        state["processing_status"] = "attending"
        return state
    
    async def process_document(self, state: DPACognitiveState) -> DPACognitiveState:
        """处理文档 - S2语义分块"""
        logger.info("Processing document with S2 chunking...")
        
        # 这里应该调用S2分块器
        # 现在使用简化实现
        document = state["sensory_buffer"].get("current_input", {}).get("content", "")
        
        # 模拟S2分块
        chunks = []
        chunk_size = 1000  # 简化版
        for i in range(0, len(document), chunk_size):
            chunk = {
                "id": f"chunk_{i}",
                "content": document[i:i+chunk_size],
                "start": i,
                "end": min(i+chunk_size, len(document)),
                "metadata": {
                    "chunk_index": len(chunks),
                    "semantic_density": 0.8  # 模拟值
                }
            }
            chunks.append(chunk)
        
        state["s2_chunks"] = chunks
        state["processing_status"] = "document_processed"
        
        return state
    
    async def extract_to_graph(self, state: DPACognitiveState) -> DPACognitiveState:
        """提取知识到图谱"""
        logger.info("Extracting knowledge to graph...")
        
        extracted_docs = []
        
        for chunk in state.get("s2_chunks", [])[:5]:  # 限制处理数量
            # 提取实体和关系
            extraction_prompt = f"""
            从以下文本中提取：
            1. 关键概念（名词、专业术语）
            2. 概念之间的关系
            3. 概念的属性
            
            文本：{chunk['content'][:500]}
            
            返回JSON格式。
            """
            
            if self.mock_mode or not hasattr(self, 'llm'):
                # 模拟提取结果
                pass  # 使用简化处理
            else:
                response = await self.llm.ainvoke([HumanMessage(content=extraction_prompt)])
            
            # 简化处理
            extracted_docs.append({
                "id": f"concept_{chunk['id']}",
                "name": f"Concept from {chunk['id']}",
                "source": chunk['id'],
                "properties": {
                    "extracted_at": datetime.now().isoformat()
                }
            })
        
        state["extracted_graph_documents"] = extracted_docs
        return state
    
    async def encode_to_memory(self, state: DPACognitiveState) -> DPACognitiveState:
        """编码到记忆系统"""
        logger.info("Encoding to memory...")
        
        # 1. 将重要信息从工作记忆转入情节记忆
        important_items = [
            (k, v) for k, v in state["working_memory"].items()
            if state["attention_weights"].get(k, 0) > 0.7
        ]
        
        for key, value in important_items:
            episode = {
                "id": f"episode_{datetime.now().timestamp()}",
                "key": key,
                "value": value,
                "timestamp": datetime.now(),
                "context": {
                    "thread_id": state["thread_id"],
                    "processing_status": state["processing_status"]
                }
            }
            state["episodic_memory"].append(episode)
        
        # 2. 识别可以转为语义记忆的模式
        if len(state["episodic_memory"]) > 10:
            # 简化的模式识别
            concepts = {}
            for episode in state["episodic_memory"][-20:]:
                if "entity" in episode.get("value", {}).get("type", ""):
                    entity = episode["value"]["value"]
                    concepts[entity] = concepts.get(entity, 0) + 1
            
            # 频繁出现的转为语义记忆
            for concept, count in concepts.items():
                if count > 3:
                    state["semantic_memory"][concept] = {
                        "type": "frequent_entity",
                        "count": count,
                        "first_seen": datetime.now().isoformat()
                    }
        
        return state
    
    async def consolidate_memories(self, state: DPACognitiveState) -> DPACognitiveState:
        """巩固记忆 - 压缩和整理"""
        logger.info("Consolidating memories...")
        
        # 压缩工作记忆
        if len(state["working_memory"]) > StateManager.WORKING_MEMORY_LIMIT:
            state = self.state_manager.compress_working_memory(state)
        
        # 整理情节记忆
        if len(state["episodic_memory"]) > 100:
            # 保留最近的和重要的
            sorted_episodes = sorted(
                state["episodic_memory"],
                key=lambda x: (x.get("context", {}).get("importance", 0), x["timestamp"]),
                reverse=True
            )
            state["episodic_memory"] = sorted_episodes[:80]
        
        return state
    
    async def retrieve_from_memory(self, state: DPACognitiveState) -> DPACognitiveState:
        """从记忆中检索相关信息"""
        logger.info("Retrieving from memory...")
        
        # 这里应该实现三阶段混合检索
        # 现在使用简化版本
        
        query = state["sensory_buffer"].get("current_input", {}).get("content", "")
        
        # 模拟检索结果
        state["retrieved_context"] = {
            "semantic_matches": [],
            "episodic_matches": [],
            "graph_context": []
        }
        
        return state
    
    async def reasoning_engine(self, state: DPACognitiveState) -> DPACognitiveState:
        """推理引擎 - 基于检索结果生成理解"""
        logger.info("Reasoning...")
        
        # 构建推理上下文
        context = state.get("retrieved_context", {})
        query = state["sensory_buffer"].get("current_input", {}).get("content", "")
        
        reasoning_prompt = f"""
        基于以下上下文，回答用户问题：
        
        问题：{query}
        
        上下文：{context}
        
        请提供准确、相关的回答。
        """
        
        if self.mock_mode or not hasattr(self, 'llm'):
            # 模拟推理响应
            response_content = f"基于认知负荷理论，在教育中的应用包括：1. 管理内在认知负荷 2. 优化外在认知负荷 3. 促进相关认知负荷。这些原则有助于设计更有效的学习体验。"
        else:
            response = await self.llm.ainvoke([HumanMessage(content=reasoning_prompt)])
            response_content = response.content
        
        # 添加响应
        state["messages"].append(AIMessage(content=response_content))
        state["processing_status"] = "reasoned"
        
        return state
    
    async def identify_knowledge_gaps(self, state: DPACognitiveState) -> DPACognitiveState:
        """识别知识盲点"""
        logger.info("Identifying knowledge gaps...")
        
        # 分析当前知识状态
        gaps = []
        
        # 1. 检查未回答的问题
        if state.get("unanswered_questions"):
            for question in state["unanswered_questions"]:
                gaps.append({
                    "type": "unanswered_question",
                    "description": question,
                    "severity": "high"
                })
        
        # 2. 检查低置信度区域
        for concept, data in state.get("semantic_memory", {}).items():
            if data.get("confidence", 1.0) < 0.5:
                gaps.append({
                    "type": "low_confidence_concept",
                    "description": f"Low confidence in {concept}",
                    "severity": "medium"
                })
        
        state["knowledge_gaps"] = gaps
        return state
    
    async def generate_hypotheses(self, state: DPACognitiveState) -> DPACognitiveState:
        """生成学习假设"""
        logger.info("Generating hypotheses...")
        
        # 基于知识盲点生成假设
        hypotheses = []
        
        for gap in state.get("knowledge_gaps", [])[:5]:
            hypothesis = {
                "id": f"hyp_{datetime.now().timestamp()}",
                "content": f"Hypothesis about {gap['description']}",
                "confidence": 0.5,
                "source": "knowledge_gap_analysis",
                "created_at": datetime.now().isoformat()
            }
            hypotheses.append(hypothesis)
        
        state["learning_hypotheses"] = hypotheses
        return state
    
    async def self_evaluate(self, state: DPACognitiveState) -> DPACognitiveState:
        """自我评估 - 元认知"""
        logger.info("Self evaluating...")
        
        evaluation = {
            "timestamp": datetime.now(),
            "working_memory_usage": len(state["working_memory"]) / StateManager.WORKING_MEMORY_LIMIT,
            "episodic_memory_size": len(state["episodic_memory"]),
            "semantic_memory_size": len(state["semantic_memory"]),
            "knowledge_gaps_count": len(state["knowledge_gaps"]),
            "active_hypotheses": len(state["learning_hypotheses"]),
            "overall_confidence": 0.7  # 简化计算
        }
        
        state["self_evaluation"] = evaluation
        return state
    
    async def reflect_on_progress(self, state: DPACognitiveState) -> DPACognitiveState:
        """反思进展"""
        logger.info("Reflecting on progress...")
        
        # 分析执行历史
        recent_actions = state["execution_history"][-10:]
        
        reflection = {
            "actions_taken": len(recent_actions),
            "messages_processed": len(state["messages"]),
            "concepts_learned": len(state["semantic_memory"]),
            "hypotheses_generated": len(state["learning_hypotheses"]),
            "should_continue": True
        }
        
        state["reflection"] = reflection
        return state
    
    async def sync_with_memory_bank(self, state: DPACognitiveState) -> DPACognitiveState:
        """同步记忆库"""
        logger.info("Syncing with memory bank...")
        
        # RVUE循环
        state = await self.memory_bank.read_verify_update_execute(state)
        
        # 更新记忆库
        await self.memory_bank.update_memories(state)
        
        return state
    
    # === 路由函数 ===
    
    def route_by_input_type(self, state: DPACognitiveState) -> str:
        """根据输入类型路由"""
        input_type = state["sensory_buffer"].get("analysis", {}).get("type", "query")
        return input_type
    
    def check_working_memory(self, state: DPACognitiveState) -> str:
        """检查工作记忆状态"""
        if len(state["working_memory"]) > StateManager.WORKING_MEMORY_LIMIT:
            return "overflow"
        return "normal"
    
    def check_understanding(self, state: DPACognitiveState) -> str:
        """检查理解程度"""
        # 简化判断
        if state.get("confidence_score", 0.5) > 0.8:
            return "understood"
        elif state.get("confidence_score", 0.5) < 0.3:
            return "need_more"
        return "unclear"
    
    def evaluate_gap_severity(self, state: DPACognitiveState) -> str:
        """评估知识盲点严重程度"""
        gaps = state.get("knowledge_gaps", [])
        if not gaps:
            return "none"
        
        critical_gaps = [g for g in gaps if g.get("severity") == "high"]
        if critical_gaps:
            return "critical"
        return "minor"
    
    def should_continue(self, state: DPACognitiveState) -> str:
        """决定是否继续"""
        reflection = state.get("reflection", {})
        
        if not reflection.get("should_continue", True):
            return "complete"
        
        if state.get("self_evaluation", {}).get("overall_confidence", 0) < 0.3:
            return "adapt"
        
        return "continue"
    
    # === 其他节点实现（占位） ===
    
    async def semantic_understanding(self, state: DPACognitiveState) -> DPACognitiveState:
        """语义理解"""
        return state
    
    async def create_learning_plan(self, state: DPACognitiveState) -> DPACognitiveState:
        """创建学习计划"""
        return state
    
    async def execute_planned_action(self, state: DPACognitiveState) -> DPACognitiveState:
        """执行计划的行动"""
        return state
    
    async def verify_hypothesis(self, state: DPACognitiveState) -> DPACognitiveState:
        """验证假设"""
        return state
    
    async def evaluate_performance(self, state: DPACognitiveState) -> DPACognitiveState:
        """评估性能"""
        return state
    
    async def adapt_strategy(self, state: DPACognitiveState) -> DPACognitiveState:
        """适应策略"""
        return state
    
    async def update_dynamic_summary(self, state: DPACognitiveState) -> DPACognitiveState:
        """更新动态摘要"""
        return state


# 工厂函数
def create_cognitive_workflow(config: Optional[Dict[str, Any]] = None) -> CognitiveWorkflow:
    """创建认知工作流实例"""
    return CognitiveWorkflow(config)