"""
MVP认知工作流 - 基于LangGraph的状态机实现
实现基础的认知循环：感知→处理→检索→推理→更新
"""
import asyncio
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime
import uuid

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver  # 使用内存检查点，避免PostgreSQL依赖
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

from src.core.memory.mvp_state import (
    MVPCognitiveState, 
    create_initial_state,
    WorkingMemoryManager,
    StateValidator,
    get_namespace_for_state,
    DEFAULT_USER_ID
)
from src.services.memory_write_service_v2 import MemoryWriteService, MemoryType
from src.database.qdrant import get_qdrant_manager
from src.services.cache_service import CacheService
from src.core.memory.memory_bank_manager import create_memory_bank_manager
from src.config.settings import settings
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


class MVPCognitiveWorkflow:
    """MVP认知工作流管理器"""
    
    def __init__(self, user_id: str = DEFAULT_USER_ID):
        self.user_id = user_id
        self.memory_service = MemoryWriteService(user_id=user_id)
        self.memory_bank_manager = create_memory_bank_manager(user_id=user_id)
        self.qdrant_manager = QdrantManager()
        self.cache_service = CacheService()
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",  # 使用OpenAI模型
            temperature=0.7,
            api_key=settings.ai_model.openai_api_key
        )
        
        # PostgreSQL检查点存储
        self.checkpointer = None
        self._init_checkpointer()
        
    def _init_checkpointer(self):
        """初始化检查点存储"""
        # MVP阶段使用内存存储，避免外部依赖
        self.checkpointer = MemorySaver()
        logger.info("Using memory checkpointer for MVP")
            
    def build_workflow(self) -> StateGraph:
        """构建认知工作流"""
        workflow = StateGraph(MVPCognitiveState)
        
        # 添加节点
        workflow.add_node("perceive", self._perceive_node)
        workflow.add_node("process", self._process_node)
        workflow.add_node("retrieve", self._retrieve_node)
        workflow.add_node("reason", self._reason_node)
        workflow.add_node("update_memory", self._update_memory_node)
        
        # 设置入口点
        workflow.set_entry_point("perceive")
        
        # 添加边（包含条件路由）
        workflow.add_edge("perceive", "process")
        workflow.add_conditional_edges(
            "process",
            self._should_retrieve,
            {
                "retrieve": "retrieve",
                "reason": "reason"
            }
        )
        workflow.add_edge("retrieve", "reason")
        workflow.add_conditional_edges(
            "reason",
            self._should_update_memory,
            {
                "update": "update_memory",
                "end": END
            }
        )
        workflow.add_edge("update_memory", END)
        
        # 编译工作流
        return workflow.compile(checkpointer=self.checkpointer)
        
    async def _perceive_node(self, state: MVPCognitiveState) -> MVPCognitiveState:
        """感知节点 - 接收和理解输入"""
        logger.info(f"Perceive node - User: {state['user_id']}")
        
        # 获取最新消息
        if not state["messages"]:
            state["last_error"] = "No input messages"
            state["processing_status"] = "failed"
            return state
            
        last_message = state["messages"][-1]
        
        # 提取意图和实体
        intent_prompt = f"""
        分析用户输入，提取：
        1. 意图类型（query/learn/analyze/summarize）
        2. 关键实体
        3. 所需上下文
        
        用户输入：{last_message.content}
        """
        
        try:
            response = await self.llm.ainvoke(intent_prompt)
            analysis = response.content
            
            # 更新工作记忆
            state = WorkingMemoryManager.add_item(
                state,
                "current_intent",
                {
                    "raw_input": last_message.content,
                    "analysis": analysis,
                    "timestamp": datetime.now().isoformat()
                },
                priority=10
            )
            
            state["processing_status"] = "processing"
            state["updated_at"] = datetime.now()
            
        except Exception as e:
            logger.error(f"Perceive node error: {e}")
            state["last_error"] = str(e)
            state["processing_status"] = "failed"
            
        return state
        
    async def _process_node(self, state: MVPCognitiveState) -> MVPCognitiveState:
        """处理节点 - 处理文档或准备查询"""
        logger.info(f"Process node - User: {state['user_id']}")
        
        intent = WorkingMemoryManager.get_item(state, "current_intent")
        if not intent:
            state["last_error"] = "No intent found"
            return state
            
        # 如果有待处理的文档
        if state.get("current_chunk"):
            try:
                chunk = state["current_chunk"]
                
                # 写入到所有存储系统
                result = await self.memory_service.write_memory(
                    content=chunk["content"],
                    memory_type=MemoryType.SEMANTIC,
                    metadata={
                        "source": chunk.get("source", "unknown"),
                        "chunk_index": chunk.get("index", 0)
                    },
                    project_id=state.get("project_id"),
                    user_id=state["user_id"]
                )
                
                if result.success:
                    # 添加到最近文档列表
                    recent_docs = state.get("recent_documents", [])
                    recent_docs.append({
                        "operation_id": result.operation_id,
                        "content_preview": chunk["content"][:200],
                        "timestamp": datetime.now().isoformat()
                    })
                    # 保持最近10个
                    state["recent_documents"] = recent_docs[-10:]
                    
                state["current_chunk"] = None
                
            except Exception as e:
                logger.error(f"Document processing error: {e}")
                state["last_error"] = str(e)
                
        return state
        
    async def _retrieve_node(self, state: MVPCognitiveState) -> MVPCognitiveState:
        """检索节点 - 三阶段混合检索"""
        logger.info(f"Retrieve node - User: {state['user_id']}")
        
        intent = WorkingMemoryManager.get_item(state, "current_intent")
        if not intent:
            return state
            
        query = intent["raw_input"]
        
        # 检查缓存
        cache_key = f"{state['user_id']}:query:{query}"
        cached_result = await self.cache_service.get(cache_key)
        if cached_result:
            state["query_result"] = cached_result
            return state
            
        try:
            # Stage 1: 向量搜索
            namespace = get_namespace_for_state(state)
            vector_results = await self._vector_search(query, namespace)
            
            # Stage 2: 图扩展（简化版 - 仅使用相关文档ID）
            expanded_results = await self._expand_with_graph(vector_results)
            
            # Stage 3: Memory Bank增强
            memory_context = await self._enhance_with_memory_bank(
                query, 
                state["user_id"], 
                state.get("project_id")
            )
            
            # 融合结果
            query_result = {
                "vector_results": vector_results[:5],
                "expanded_results": expanded_results[:3],
                "memory_context": memory_context,
                "total_results": len(vector_results) + len(expanded_results)
            }
            
            state["query_result"] = query_result
            
            # 缓存结果
            await self.cache_service.set(cache_key, query_result, ttl=1800)
            
            # 更新工作记忆
            state = WorkingMemoryManager.add_item(
                state,
                f"retrieval_{datetime.now().timestamp()}",
                {
                    "query": query,
                    "results_count": query_result["total_results"]
                },
                priority=5
            )
            
        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            state["last_error"] = str(e)
            state["query_result"] = {"error": str(e)}
            
        return state
        
    async def _reason_node(self, state: MVPCognitiveState) -> MVPCognitiveState:
        """推理节点 - 基于检索结果生成响应"""
        logger.info(f"Reason node - User: {state['user_id']}")
        
        intent = WorkingMemoryManager.get_item(state, "current_intent")
        query_result = state.get("query_result", {})
        
        if not intent:
            return state
            
        # 构建上下文
        context_parts = []
        
        # 添加向量搜索结果
        if "vector_results" in query_result:
            for result in query_result["vector_results"]:
                context_parts.append(f"[相关内容] {result.get('content', '')}")
                
        # 添加Memory Bank上下文
        if "memory_context" in query_result:
            mem_ctx = query_result["memory_context"]
            if mem_ctx.get("current_context"):
                context_parts.append(f"[当前上下文] {mem_ctx['current_context']}")
                
        context = "\n\n".join(context_parts)
        
        # 生成响应
        reasoning_prompt = f"""
        基于以下上下文回答用户问题：
        
        上下文：
        {context}
        
        用户问题：{intent['raw_input']}
        
        请提供准确、相关的回答。
        """
        
        try:
            response = await self.llm.ainvoke(reasoning_prompt)
            
            # 添加AI消息
            ai_message = AIMessage(content=response.content)
            state["messages"].append(ai_message)
            
            # 更新工作记忆
            state = WorkingMemoryManager.add_item(
                state,
                "last_response",
                {
                    "content": response.content,
                    "timestamp": datetime.now().isoformat(),
                    "context_used": len(context_parts)
                },
                priority=8
            )
            
            state["processing_status"] = "completed"
            
        except Exception as e:
            logger.error(f"Reasoning error: {e}")
            state["last_error"] = str(e)
            state["processing_status"] = "failed"
            
        return state
        
    async def _update_memory_node(self, state: MVPCognitiveState) -> MVPCognitiveState:
        """更新记忆节点 - 将新知识写入记忆系统"""
        logger.info(f"Update memory node - User: {state['user_id']}")
        
        last_response = WorkingMemoryManager.get_item(state, "last_response")
        current_intent = WorkingMemoryManager.get_item(state, "current_intent")
        
        if not last_response or not current_intent:
            return state
            
        project_id = state.get("project_id")
        if not project_id:
            return state
            
        try:
            # 提取关键概念
            extraction_prompt = f"""
            从以下对话中提取关键概念和实体。
            
            问题：{current_intent['raw_input']}
            回答：{last_response['content']}
            
            请识别：
            1. 关键概念（名词、专业术语）
            2. 概念之间的关系
            3. 概念的类别（技术/理论/应用/其他）
            
            返回JSON格式：
            {{
                "concepts": [
                    {{"name": "概念名", "category": "类别", "description": "简短描述"}}
                ],
                "relationships": [
                    {{"from": "概念1", "to": "概念2", "type": "关系类型"}}
                ]
            }}
            """
            
            extraction_response = await self.llm.ainvoke(extraction_prompt)
            
            # 解析提取结果
            try:
                import json
                import re
                # 提取JSON内容
                json_match = re.search(r'\{[\s\S]*\}', extraction_response.content)
                if json_match:
                    extracted_data = json.loads(json_match.group())
                else:
                    extracted_data = {"concepts": [], "relationships": []}
            except:
                extracted_data = {"concepts": [], "relationships": []}
            
            # 更新Memory Bank
            # 1. 更新上下文
            qa_content = f"Q: {current_intent['raw_input']}\nA: {last_response['content']}"
            await self.memory_bank_manager.update_context(
                project_id=project_id,
                new_content=qa_content,
                source="qa_interaction"
            )
            
            # 2. 添加概念
            if extracted_data.get("concepts"):
                await self.memory_bank_manager.add_concepts(
                    project_id=project_id,
                    new_concepts=extracted_data["concepts"]
                )
            
            # 3. 触发摘要更新（异步，不等待）
            asyncio.create_task(
                self.memory_bank_manager.update_summary(project_id)
            )
            
            # 写入持久化记忆
            await self.memory_service.write_memory(
                content=qa_content,
                memory_type=MemoryType.EPISODIC,
                metadata={
                    "interaction_type": "qa",
                    "timestamp": last_response["timestamp"],
                    "concepts": extracted_data.get("concepts", [])
                },
                project_id=project_id,
                user_id=state["user_id"],
                entities=extracted_data.get("concepts", []),
                relationships=extracted_data.get("relationships", [])
            )
            
            # 获取最新的Memory Bank快照
            snapshot = await self.memory_bank_manager.get_snapshot(project_id)
            
            # 更新状态
            state["memory_bank_snapshot"] = {
                "last_updated": datetime.now().isoformat(),
                "concepts_count": snapshot.get("concepts_count", 0),
                "interactions_count": snapshot.get("metadata", {}).get("stats", {}).get("total_interactions", 0),
                "summary_preview": snapshot.get("summary", "")[:200] + "..." if snapshot.get("summary") else ""
            }
            
        except Exception as e:
            logger.error(f"Memory update error: {e}")
            state["last_error"] = str(e)
            
        return state
        
    def _should_retrieve(self, state: MVPCognitiveState) -> Literal["retrieve", "reason"]:
        """判断是否需要检索"""
        intent = WorkingMemoryManager.get_item(state, "current_intent")
        if not intent:
            return "reason"
            
        # 如果是查询类意图，需要检索
        if "query" in intent.get("analysis", "").lower():
            return "retrieve"
            
        return "reason"
        
    def _should_update_memory(self, state: MVPCognitiveState) -> Literal["update", "end"]:
        """判断是否需要更新记忆"""
        # 如果有生成的响应，更新记忆
        if WorkingMemoryManager.get_item(state, "last_response"):
            return "update"
        return "end"
        
    async def _vector_search(self, query: str, namespace: str) -> List[Dict[str, Any]]:
        """向量搜索"""
        # 这里应该调用实际的向量搜索
        # 现在返回模拟结果
        return [
            {
                "id": str(uuid.uuid4()),
                "content": "相关文档内容1",
                "score": 0.95
            },
            {
                "id": str(uuid.uuid4()),
                "content": "相关文档内容2", 
                "score": 0.88
            }
        ]
        
    async def _expand_with_graph(self, vector_results: List[Dict]) -> List[Dict]:
        """图扩展（简化版）"""
        # MVP版本：直接返回空列表
        # 未来实现：基于vector_results中的ID查询Neo4j
        return []
        
    async def _enhance_with_memory_bank(
        self, 
        query: str, 
        user_id: str, 
        project_id: Optional[str]
    ) -> Dict[str, Any]:
        """Memory Bank增强"""
        if not project_id:
            return {}
            
        try:
            # 获取项目快照
            snapshot = await self.memory_bank_manager.get_snapshot(project_id)
            
            if not snapshot:
                # 如果项目不存在，初始化它
                await self.memory_bank_manager.initialize_project(project_id)
                return {}
                
            # 搜索相关概念
            relevant_concepts = await self.memory_bank_manager.search_concepts(
                project_id=project_id,
                query=query
            )
            
            return {
                "current_context": snapshot.get("context_preview", ""),
                "summary": snapshot.get("summary", ""),
                "relevant_concepts": [c["name"] for c in relevant_concepts[:5]],
                "total_concepts": snapshot.get("concepts_count", 0),
                "last_updated": snapshot.get("last_updated", "")
            }
            
        except Exception as e:
            logger.error(f"Memory Bank enhancement error: {e}")
            return {}
        
    async def run(
        self,
        message: str,
        thread_id: Optional[str] = None,
        project_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> MVPCognitiveState:
        """运行工作流"""
        # 创建初始状态
        initial_state = create_initial_state(
            user_id=self.user_id,
            project_id=project_id,
            thread_id=thread_id
        )
        
        # 添加用户消息
        initial_state["messages"] = [HumanMessage(content=message)]
        
        # 构建配置
        if not config:
            config = {}
        config["configurable"] = {
            "thread_id": initial_state["thread_id"],
            "user_id": self.user_id
        }
        
        # 构建并运行工作流
        workflow = self.build_workflow()
        
        try:
            # 运行工作流
            final_state = await workflow.ainvoke(initial_state, config)
            
            # 验证最终状态
            if not StateValidator.validate_state(final_state):
                final_state = StateValidator.sanitize_state(final_state)
                
            return final_state
            
        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            initial_state["last_error"] = str(e)
            initial_state["processing_status"] = "failed"
            return initial_state


# 工厂函数
def create_mvp_workflow(user_id: str = DEFAULT_USER_ID) -> MVPCognitiveWorkflow:
    """创建MVP认知工作流实例"""
    return MVPCognitiveWorkflow(user_id=user_id)