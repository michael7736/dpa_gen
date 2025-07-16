"""
MVP问答系统 - 集成混合检索
使用三阶段检索增强的问答系统
"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.prompts import PromptTemplate

from src.core.retrieval.mvp_hybrid_retriever import create_mvp_hybrid_retriever
from src.services.memory_write_service_v2 import MemoryWriteService, MemoryType
from src.core.memory.memory_bank_manager import create_memory_bank_manager
from src.config.settings import settings
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

# 默认配置
DEFAULT_USER_ID = "u1"
DEFAULT_MODEL = "gpt-4o-mini"


@dataclass
class QAResult:
    """问答结果"""
    question: str
    answer: str
    context_used: List[Dict[str, Any]]
    retrieval_breakdown: Dict[str, int]
    confidence_score: float
    processing_time: float
    metadata: Dict[str, Any]


class MVPQASystem:
    """
    MVP问答系统
    集成三阶段混合检索的RAG系统
    """
    
    def __init__(self, user_id: str = DEFAULT_USER_ID):
        self.user_id = user_id
        self.retriever = create_mvp_hybrid_retriever(user_id=user_id)
        self.memory_service = MemoryWriteService(user_id=user_id)
        self.memory_bank_manager = create_memory_bank_manager(user_id=user_id)
        
        # LLM配置
        self.llm = ChatOpenAI(
            model=DEFAULT_MODEL,
            temperature=0.1,
            max_tokens=2000,
            api_key=settings.ai_model.openai_api_key
        )
        
        # 提示词模板
        self.qa_prompt = PromptTemplate(
            input_variables=["context", "question", "memory_context"],
            template="""基于以下上下文信息回答问题。如果上下文中没有相关信息，请说明这一点。

检索到的文档：
{context}

记忆库信息：
{memory_context}

问题：{question}

请提供准确、详细的回答。如果信息不足，请明确指出。
"""
        )
        
        self.confidence_prompt = PromptTemplate(
            input_variables=["answer", "context_relevance"],
            template="""评估以下回答的置信度（0-1分）：

回答：{answer}

上下文相关性：{context_relevance}

仅返回一个0到1之间的数字，表示回答的置信度。
"""
        )
        
    async def answer_question(
        self,
        question: str,
        project_id: Optional[str] = None,
        top_k: int = 10,
        include_memory: bool = True
    ) -> QAResult:
        """
        回答问题
        
        Args:
            question: 用户问题
            project_id: 项目ID
            top_k: 检索结果数量
            include_memory: 是否包含记忆库信息
            
        Returns:
            QAResult: 问答结果
        """
        start_time = datetime.now()
        
        try:
            # 1. 执行混合检索
            retrieval_result = await self.retriever.retrieve(
                query=question,
                project_id=project_id,
                top_k=top_k,
                score_threshold=0.6
            )
            
            # 2. 准备上下文
            context = self._format_retrieval_context(retrieval_result.fused_results)
            
            # 3. 获取Memory Bank上下文
            memory_context = ""
            if include_memory and project_id:
                memory_snapshot = await self.memory_bank_manager.get_snapshot(project_id)
                if memory_snapshot:
                    memory_context = self._format_memory_context(memory_snapshot)
                    
            # 4. 生成回答
            answer = await self._generate_answer(question, context, memory_context)
            
            # 5. 评估置信度
            confidence = await self._evaluate_confidence(
                answer,
                len(retrieval_result.fused_results),
                retrieval_result.fused_results[0].score if retrieval_result.fused_results else 0
            )
            
            # 6. 保存交互记录
            if project_id:
                await self._save_interaction(project_id, question, answer)
                
            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return QAResult(
                question=question,
                answer=answer,
                context_used=[
                    {
                        "doc_id": r.doc_id,
                        "content": r.content[:200] + "..." if len(r.content) > 200 else r.content,
                        "score": r.score,
                        "source": r.source
                    }
                    for r in retrieval_result.fused_results[:5]
                ],
                retrieval_breakdown={
                    "vector": len(retrieval_result.vector_results),
                    "graph": len(retrieval_result.graph_results),
                    "memory": len(retrieval_result.memory_results)
                },
                confidence_score=confidence,
                processing_time=processing_time,
                metadata={
                    "project_id": project_id,
                    "user_id": self.user_id,
                    "model": DEFAULT_MODEL,
                    "retrieval_time": retrieval_result.retrieval_time
                }
            )
            
        except Exception as e:
            logger.error(f"QA error: {e}")
            raise
            
    async def _generate_answer(
        self,
        question: str,
        context: str,
        memory_context: str
    ) -> str:
        """生成回答"""
        prompt = self.qa_prompt.format(
            context=context,
            memory_context=memory_context,
            question=question
        )
        
        messages = [
            SystemMessage(content="你是一个专业的问答助手，基于提供的上下文准确回答问题。"),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
        
    async def _evaluate_confidence(
        self,
        answer: str,
        context_count: int,
        top_score: float
    ) -> float:
        """评估回答置信度"""
        # 简单的置信度计算
        base_confidence = 0.5
        
        # 基于检索结果数量
        if context_count > 5:
            base_confidence += 0.2
        elif context_count > 0:
            base_confidence += 0.1
            
        # 基于最高分数
        if top_score > 0.8:
            base_confidence += 0.2
        elif top_score > 0.7:
            base_confidence += 0.1
            
        # 基于回答长度
        if len(answer) > 100:
            base_confidence += 0.1
            
        return min(base_confidence, 0.95)
        
    def _format_retrieval_context(self, results: List) -> str:
        """格式化检索结果为上下文"""
        if not results:
            return "未找到相关文档。"
            
        context_parts = []
        for i, result in enumerate(results[:5]):  # 只使用前5个结果
            context_parts.append(
                f"[文档{i+1} - 来源:{result.source} - 相关度:{result.score:.2f}]\n"
                f"{result.content}\n"
            )
            
        return "\n\n".join(context_parts)
        
    def _format_memory_context(self, snapshot: Dict[str, Any]) -> str:
        """格式化Memory Bank信息"""
        parts = []
        
        if snapshot.get("dynamic_summary"):
            parts.append(f"项目摘要：\n{snapshot['dynamic_summary']}")
            
        if snapshot.get("core_concepts"):
            concepts = [c["name"] for c in snapshot["core_concepts"][:5]]
            parts.append(f"核心概念：{', '.join(concepts)}")
            
        return "\n\n".join(parts) if parts else "无记忆库信息"
        
    async def _save_interaction(
        self,
        project_id: str,
        question: str,
        answer: str
    ):
        """保存交互记录"""
        try:
            # 保存到记忆系统
            interaction = f"Q: {question}\nA: {answer}"
            
            await self.memory_service.write_memory(
                content=interaction,
                memory_type=MemoryType.WORKING,
                metadata={
                    "type": "qa_interaction",
                    "question": question,
                    "timestamp": datetime.now().isoformat()
                },
                project_id=project_id,
                user_id=self.user_id
            )
            
            # 更新Memory Bank学习日志
            await self.memory_bank_manager.add_learning_entry(
                project_id=project_id,
                content=f"问答交互：{question[:50]}...",
                learning_type="qa",
                metadata={"full_question": question}
            )
            
        except Exception as e:
            logger.error(f"Failed to save interaction: {e}")
            # 不中断主流程
            
    async def batch_answer(
        self,
        questions: List[str],
        project_id: Optional[str] = None,
        max_concurrent: int = 3
    ) -> List[QAResult]:
        """批量回答问题"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def answer_with_limit(question: str) -> QAResult:
            async with semaphore:
                return await self.answer_question(question, project_id)
                
        tasks = [answer_with_limit(q) for q in questions]
        return await asyncio.gather(*tasks)
        
    async def answer_with_context(
        self,
        question: str,
        additional_context: str,
        project_id: Optional[str] = None
    ) -> QAResult:
        """带额外上下文的问答"""
        # 将额外上下文添加到问题中
        enhanced_question = f"{question}\n\n补充信息：{additional_context}"
        
        return await self.answer_question(
            enhanced_question,
            project_id,
            top_k=15  # 检索更多结果
        )


# 工厂函数
def create_mvp_qa_system(user_id: str = DEFAULT_USER_ID) -> MVPQASystem:
    """创建MVP问答系统实例"""
    return MVPQASystem(user_id=user_id)